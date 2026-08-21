import re
from typing import Optional, Tuple, Dict, Any, List
import erpnext_tools

# 1. 색상 별칭 사전 (스페인어/한국어/영어 통합)
COLOR_ALIASES = {
    '네그로': 'NEGRO', 'negro': 'NEGRO', '검정': 'NEGRO', '검정색': 'NEGRO', '블랙': 'NEGRO', 'black': 'NEGRO',
    '베이지': 'BEIGE', 'beige': 'BEIGE',
    '블랑코': 'BLANCO', 'blanco': 'BLANCO', '화이트': 'BLANCO', '하얀': 'BLANCO', '흰색': 'BLANCO', 'white': 'BLANCO',
    '로호': 'ROJO', 'rojo': 'ROJO', '빨강': 'ROJO', '빨간색': 'ROJO', 'red': 'ROJO',
    '아술': 'AZUL', 'azul': 'AZUL', '파랑': 'AZUL', '파란색': 'AZUL', 'blue': 'AZUL',
    '마리노': 'MARINO', 'marino': 'MARINO', '곤색': 'MARINO', '남색': 'MARINO', 'navy': 'MARINO',
    '수르티도': 'SURTIDO', 'surtido': 'SURTIDO', '혼합': 'SURTIDO'
}

# 2. 한글 수사 -> 아라비아 숫자 변환 딕셔너리
KO_DIGITS = {
    '영': 0, '공': 0, '일': 1, '한': 1, '하나': 1, '이': 2, '두': 2, '둘': 2,
    '삼': 3, '세': 3, '셋': 3, '사': 4, '네': 4, '넷': 4, '오': 5, '다섯': 5,
    '육': 6, '여섯': 6, '칠': 7, '일곱': 7, '팔': 8, '여덟': 8, '구': 9, '아홉': 9
}

def spoken_numerals_to_digits(text: str) -> str:
    """
    텍스트/발화 내 한글 수사를 아라비아 숫자로 변환 (예: "삼삼삼일 네그로" -> "3331 NEGRO")
    """
    if not text:
        return ""
    
    s = text.strip()
    
    # 3음절 이상의 연속된 한글 숫자 ("삼삼삼일" -> "3331")
    def replace_digit_seq(match):
        seq = match.group(0)
        digits = [str(KO_DIGITS[ch]) for ch in seq if ch in KO_DIGITS]
        return "".join(digits) if len(digits) >= 2 else seq

    s = re.sub(r'[영공일이삼사오육칠팔구]{2,}', replace_digit_seq, s)
    
    # 색상 별칭 치환
    for alias, standard in COLOR_ALIASES.items():
        # 단어 경계 또는 포함 매칭
        s = re.sub(rf'\b{alias}\b', standard, s, flags=re.IGNORECASE)

    return s

def try_zero_token_local_bypass(text: str, sender_name: str = "사용자") -> Optional[str]:
    """
    [Tier 0: 토큰 0개 로컬 바이패스 엔진]
    단순 정형 패턴(도움말, 창고 목록, 인사, 단순 재고조회)을 LLM 없이 0토큰/0.01초로 즉시 응답.
    LLM 호출이 필요하면 None을 반환하여 Gemini로 위임합니다.
    """
    cleaned = text.strip()
    norm = spoken_numerals_to_digits(cleaned).lower()

    # 1. 인사 패턴
    if norm in ['안녕', '안녕하세요', '하이', 'hola', 'buenas', 'buenos dias', 'buenas tardes']:
        return f"👋 안녕하세요, {sender_name}님! KTK WMS AI 에이전트입니다.\n\n재고 조회, 품목 검색, 창고 목록 등을 언제든 물어보세요!\n(예: '021G 재고', '창고 목록', '025G 검색')"

    # 2. 도움말 / 명령어
    if norm in ['도움말', '명령어', '사용법', 'help', 'ayuda']:
        return (
            "📋 **KTK WMS WhatsApp 비서 사용 안내**\n\n"
            "• **재고 조회:** `021G-AZUL-400 재고`, `3331 네그로 재고`\n"
            "• **품목 검색:** `025G 검색`, `P-D60 찾아줘`\n"
            "• **창고 목록:** `창고 목록`, `지점 보여줘`\n"
            "• **단가 확인:** `021G 가격`, `단가 알려줘`\n\n"
            "한국어와 스페인어 모두 편하게 자연어로 입력하시면 됩니다!"
        )

    # 3. 창고 목록 단순 요청
    if norm in ['창고 목록', '창고목록', '지점 목록', '지점목록', '창고', 'almacenes', 'sucursales', 'ver almacenes']:
        warehouses = erpnext_tools.get_warehouses()
        if not warehouses:
            return "현재 등록된 활성 창고 정보가 없습니다."
        
        lines = ["🏬 **KTK WMS 활성 창고 목록**\n"]
        for w in warehouses:
            lines.append(f"• **{w.get('name')}** ({w.get('warehouse_name', '')})")
        return "\n".join(lines)

    # 4. 명확한 품목 코드 재고 조회 패턴 (예: "021G-AZUL-400 재고", "P-D60 재고 얼마")
    # 품목코드 규격: 영문/숫자-영문/숫자 형태가 명확하고 '재고' 또는 'stock' 키워드가 있을 때
    match = re.search(r'([A-Za-z0-9]+-[A-Za-z0-9\-]+)\s*(재고|stock|cuanto hay|existencia)?', cleaned, re.IGNORECASE)
    if match and any(k in norm for k in ['재고', 'stock', 'existencia', 'cuanto']):
        item_code = match.group(1).upper()
        stock_info = erpnext_tools.get_item_stock(item_code)
        
        if stock_info.get("success") and stock_info.get("total_qty") is not None:
            total_qty = int(stock_info['total_qty'])
            pack = stock_info.get('pack_qty', 1)
            boxes = stock_info.get('total_boxes', 0)
            eaches = stock_info.get('total_eaches', 0)
            
            res_lines = [
                f"📌 **[{item_code}] 실시간 재고 현황**",
                f"📦 **총 재고량:** {boxes}박스 ({total_qty:,}개)" if pack > 1 else f"📦 **총 재고량:** {total_qty:,}개",
                f"*(입수량: 1박스당 {pack}개)*\n",
                "📍 **창고별 상세:**"
            ]
            
            wh_list = stock_info.get("warehouses", [])
            if not wh_list or all(w.get('actual_qty', 0) <= 0 for w in wh_list):
                res_lines.append("• 현재 보유 중인 재고가 없습니다. (0개)")
            else:
                for w in wh_list:
                    w_qty = int(w.get('actual_qty', 0))
                    if w_qty > 0:
                        w_box = w.get('boxes', 0)
                        w_each = w.get('eaches', 0)
                        box_str = f"{w_box}박스" if w_box > 0 else ""
                        each_str = f"{w_each}개" if w_each > 0 or not box_str else ""
                        qty_detail = f"{box_str} {each_str}".strip()
                        res_lines.append(f"• **{w.get('warehouse')}**: {qty_detail} (총 {w_qty:,}개)")
            
            return "\n".join(res_lines)

    # 단순 로컬 처리 대상이 아니면 LLM(Gemini)으로 넘김
    return None
