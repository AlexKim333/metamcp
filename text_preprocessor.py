import re
from typing import Optional, Tuple, Dict, Any, List
import erpnext_tools

# 1. 색상 별칭 사전 (스페인어/한국어/영어 통합)
COLOR_ALIASES = {
    '네그로': 'NEGRO', 'negro': 'NEGRO', '검정': 'NEGRO', '검정색': 'NEGRO', '블랙': 'NEGRO', 'black': 'NEGRO',
    '베이지': 'BEIGE', 'beige': 'BEIGE',
    '블랑코': 'BLANCO', 'blanco': 'BLANCO', '화이트': 'BLANCO', '하얀': 'BLANCO', '흰색': 'BLANCO', 'white': 'BLANCO',
    '로호': 'ROJO', 'rojo': 'ROJO', '빨강': 'ROJO', '빨강색': 'ROJO', '빨간색': 'ROJO', 'red': 'ROJO',
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
        s = re.sub(rf'\b{alias}\b', standard, s, flags=re.IGNORECASE)

    return s

def try_zero_token_local_bypass(text: str, sender_name: str = "사용자") -> Optional[str]:
    """
    [Tier 0: 토큰 0개 로컬 바이패스 엔진 (0.1초 초고속 즉답)]
    """
    cleaned = text.strip()
    norm = spoken_numerals_to_digits(cleaned).lower()

    # 1. 인사말
    if norm in ['hola', 'buenas', 'buenos dias', 'buenas tardes', 'buenas noches', 'que tal', 'hola!']:
        return (
            f"👋 ¡Hola, {sender_name}! Soy el **Asistente AI de KTK WMS**.\n\n"
            "¿En qué puedo ayudarte hoy?\n"
            "• **Consultar existencias:** `stock de 021G`, `existencia P160`\n"
            "• **Buscar artículos:** `buscar 025G`\n"
            "• **Ver almacenes:** `almacenes` o `sucursales`"
        )
    if norm in ['안녕', '안녕하세요', '하이', '반가워', '안뇽', '대화 가능한가', '대화 가능한가요', '대화 가능해']:
        return f"👋 안녕하세요, {sender_name}님! KTK WMS AI 에이전트입니다.\n\n재고 조회, 품목 검색, 창고 목록 등을 언제든 물어보세요!\n(예: 'P160 검정 재고', '창고 목록', '021G 재고')"

    # 2. 도움말
    if norm in ['ayuda', 'help', 'comandos', 'instrucciones']:
        return (
            "📋 **Guía del Asistente KTK WMS en WhatsApp**\n\n"
            "• **Existencias:** `021G-AZUL-400 stock`, `stock de 3331 NEGRO`\n"
            "• **Búsqueda:** `buscar 025G`, `P-D60`\n"
            "• **Almacenes:** `almacenes`, `ver sucursales`\n"
            "• **Precios:** `precio de 021G`"
        )
    if norm in ['도움말', '명령어', '사용법']:
        return (
            "📋 **KTK WMS WhatsApp 비서 사용 안내**\n\n"
            "• **재고 조회:** `021G-AZUL-400 재고`, `P160 빨강 재고`\n"
            "• **품목 검색:** `025G 검색`, `P-D60 찾아줘`\n"
            "• **창고 목록:** `창고 목록`, `지점 보여줘`\n"
            "• **단가 확인:** `021G 가격`, `단가 알려줘`"
        )

    # 3. 창고 목록
    if norm in ['almacenes', 'sucursales', 'ver almacenes', 'lista de almacenes', 'almacen']:
        warehouses = erpnext_tools.get_warehouses()
        if not warehouses:
            return "No se encontraron almacenes activos."
        lines = ["🏬 **Lista de Almacenes Activos (KTK WMS)**\n"]
        for w in warehouses:
            lines.append(f"• **{w.get('name')}** ({w.get('warehouse_name', '')})")
        return "\n".join(lines)

    if norm in ['창고 목록', '창고목록', '지점 목록', '지점목록', '창고', '지점']:
        warehouses = erpnext_tools.get_warehouses()
        if not warehouses:
            return "현재 등록된 활성 창고 정보가 없습니다."
        lines = ["🏬 **KTK WMS 활성 창고 목록**\n"]
        for w in warehouses:
            lines.append(f"• **{w.get('name')}** ({w.get('warehouse_name', '')})")
        return "\n".join(lines)

    # 4. 품목 코드/색상 기반 즉시 재고 조회 (예: "P160 빨강색 재고", "P160 ROJO stock", "021G-AZUL-400 재고")
    has_stock_query = any(k in norm for k in ['재고', 'stock', 'existencia', 'cuanto', 'cuánto', '몇개', '몇 개'])
    if has_stock_query:
        # 단어 분리
        tokens = spoken_numerals_to_digits(cleaned).replace('?', '').replace('!', '').split()
        
        code_hint = ""
        color_hint = ""
        
        for t in tokens:
            t_upper = t.upper().strip()
            # 색상 매칭
            for k_alias, std_val in COLOR_ALIASES.items():
                if k_alias.upper() == t_upper or std_val == t_upper:
                    color_hint = std_val
                    break
            # 코드 매칭 (영문/숫자 조합 또는 2자리 이상 숫자)
            clean_t = re.sub(r'[^A-Z0-9\-]', '', t_upper)
            if clean_t and clean_t not in COLOR_ALIASES.values():
                if re.search(r'\d+', clean_t) or len(clean_t) >= 3:
                    if not any(stop in clean_t for stop in ['재고', 'STOCK', 'EXISTENCIA', 'CUANTO', 'CUANTO', '몇개']):
                        code_hint = clean_t

        if code_hint:
            # P160 -> P-160 등 하이픈 변형 검색 지원
            search_queries = [code_hint]
            if re.match(r'^[A-Z]\d+', code_hint):
                search_queries.append(f"{code_hint[0]}-{code_hint[1:]}")
            
            items = []
            for sq in search_queries:
                items = erpnext_tools.search_items(sq, limit=10)
                if items:
                    break

            if items:
                if color_hint:
                    matched_items = [i for i in items if color_hint in i['name'].upper()]
                    if matched_items:
                        items = matched_items
                
                is_spanish = any(k in norm for k in ['stock', 'existencia', 'cuanto', 'cuánto', 'de', 'en'])
                res_lines = []
                
                for it in items[:3]:
                    st = erpnext_tools.get_item_stock(it['name'])
                    if st.get('success'):
                        tot_qty = int(st['total_qty'])
                        pack = st.get('pack_qty', 1)
                        boxes = st.get('total_boxes', 0)
                        eaches = st.get('total_eaches', 0)
                        wh_list = st.get('warehouses', [])
                        
                        if is_spanish:
                            res_lines.append(f"📦 **[{it['name']}]**")
                            res_lines.append(f"• **Total:** {boxes} cajas ({tot_qty:,} pzs) *(Empaque: {pack} pzs/caja)*")
                            wh_active = [w for w in wh_list if w.get('actual_qty', 0) > 0]
                            if wh_active:
                                for w in wh_active:
                                    res_lines.append(f"  📍 {w.get('warehouse')}: {w.get('boxes')} cajas ({int(w.get('actual_qty')):,} pzs)")
                            else:
                                res_lines.append("  📍 Sin existencias en almacenes.")
                        else:
                            res_lines.append(f"📦 **[{it['name']}]**")
                            res_lines.append(f"• **총 재고:** {boxes}박스 ({tot_qty:,}개) *(입수량: {pack}개/box)*")
                            wh_active = [w for w in wh_list if w.get('actual_qty', 0) > 0]
                            if wh_active:
                                for w in wh_active:
                                    res_lines.append(f"  📍 {w.get('warehouse')}: {w.get('boxes')}박스 ({int(w.get('actual_qty')):,}개)")
                            else:
                                res_lines.append("  📍 현재 보유 중인 지점 재고가 없습니다.")
                        res_lines.append("")

                if res_lines:
                    return "\n".join(res_lines).strip()

    return None
