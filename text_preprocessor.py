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

# 사용자별 언어 선호도 캐시 (전화번호 -> 'ko' | 'es')
USER_LANG_CACHE: Dict[str, str] = {}

SPANISH_SIGNALS = [
    'hola', 'buenas', 'dias', 'tardes', 'noches', 'almacen', 'almacenes',
    'stock', 'existencia', 'existencias', 'cuanto', 'cuanta', 'cuantos', 'cuantas',
    'hay', 'precio', 'precios', 'de', 'en', 'por favor', 'gracias', 'ayuda',
    'buscar', 'traspaso', 'traspasos', 'sucursal', 'sucursales', 'caja', 'cajas', 'pieza', 'piezas'
]

def spoken_numerals_to_digits(text: str) -> str:
    if not text:
        return ""
    s = text.strip()
    def replace_digit_seq(match):
        seq = match.group(0)
        digits = [str(KO_DIGITS[ch]) for ch in seq if ch in KO_DIGITS]
        return "".join(digits) if len(digits) >= 2 else seq

    s = re.sub(r'[영공일이삼사오육칠팔구]{2,}', replace_digit_seq, s)
    for alias, standard in COLOR_ALIASES.items():
        s = re.sub(rf'\b{alias}\b', standard, s, flags=re.IGNORECASE)
    return s

def detect_and_update_user_lang(phone: str, text: str) -> str:
    """
    사용자의 입력 텍스트를 분석하여 선호 언어를 감지하고 세션에 저장/유지합니다.
    - 한글이 있으면 무조건 'ko'
    - 스페인어 단어가 있으면 무조건 'es'
    - 언어가 불분명한 품목 코드/숫자만 있으면 -> 이전에 저장된 언어 유지 (기본값: 멕시코 번호 'es', 대표님 번호 'ko')
    """
    clean_p = re.sub(r'[^0-9]', '', str(phone or ''))
    raw_lower = text.lower()

    # 1. 한글 포함 여부 검사
    if re.search(r'[가-힣]', text):
        USER_LANG_CACHE[clean_p] = 'ko'
        return 'ko'

    # 2. 스페인어 신호 단어 검사
    if any(sig in raw_lower for sig in SPANISH_SIGNALS):
        USER_LANG_CACHE[clean_p] = 'es'
        return 'es'

    # 3. 기존 세션에 저장된 언어가 있으면 유지
    if clean_p in USER_LANG_CACHE:
        return USER_LANG_CACHE[clean_p]

    # 4. 기본값 설정 (5215563482005는 한국어 대표님, 그 외 멕시코 번호는 스페인어)
    default_lang = 'ko' if clean_p.endswith('5563482005') else 'es'
    USER_LANG_CACHE[clean_p] = default_lang
    return default_lang

def get_welcome_buttons_payload(sender_name: str = "사용자", is_spanish: bool = False) -> Dict[str, Any]:
    if is_spanish:
        body_text = f"👋 ¡Hola, {sender_name}! Soy el **Asistente de ladypolo**.\n\nPor favor, selecciona una opción o escribe tu consulta directamente:"
        buttons = [
            {"id": "BTN_STOCK", "title": "📦 Consultar Stock"},
            {"id": "BTN_TRANSFERS", "title": "📋 Ver Traspasos"},
            {"id": "BTN_HELP", "title": "❓ Ayuda / Info"}
        ]
    else:
        body_text = f"👋 안녕하세요, {sender_name}님! **ladypolo 비서**입니다.\n\n원하시는 업무를 아래 버튼에서 선택하시거나 편하게 질문해 주세요:"
        buttons = [
            {"id": "BTN_STOCK", "title": "📦 재고 조회"},
            {"id": "BTN_TRANSFERS", "title": "📋 최근 이동 전표"},
            {"id": "BTN_HELP", "title": "❓ 사용 안내"}
        ]
    return {
        "body_text": body_text,
        "buttons": buttons
    }

def handle_quick_button_click(button_id: str, sender_name: str = "사용자", user_lang: str = "ko") -> str:
    """[버튼 클릭 시 사용자 언어(user_lang)에 맞추어 0-Token 즉답]"""
    is_spanish = (user_lang == "es")

    if button_id == "BTN_STOCK":
        if is_spanish:
            return (
                "📦 **Consulta de Inventario**\n\n"
                "Por favor, ingresa el **código o color** del producto que deseas consultar.\n"
                "• Ejemplos: `021G`, `P160 NEGRO`, `3331`"
            )
        else:
            return (
                "📦 **재고 조회 안내**\n\n"
                "조회하고 싶으신 **품목 코드나 색상**을 입력해 주세요!\n"
                "• 예시: `021G 재고`, `P160 NEGRO`, `3331`"
            )

    elif button_id == "BTN_TRANSFERS":
        transfers = erpnext_tools.get_recent_stock_transfers(limit=5)
        if not transfers:
            return "No se encontraron traspasos recientes." if is_spanish else "📋 최근 등록된 지점 이동 전표가 없습니다."
        
        if is_spanish:
            lines = ["📋 **Traspasos de Mercancía Recientes (Últimos 5)**\n"]
            for tr in transfers:
                docstatus = tr.get("docstatus", 0)
                status_badge = "✅ Confirmado (Submit)" if docstatus == 1 else "📝 Borrador (Draft)"
                name = tr.get("name")
                date = tr.get("posting_date")
                from_wh = tr.get("from_warehouse") or "Bodega"
                to_wh = tr.get("to_warehouse") or "Bodega"
                lines.append(f"• **[{name}]** ({date}) - {status_badge}")
                lines.append(f"  Origen: {from_wh} ➔ Destino: {to_wh}\n")
            return "\n".join(lines)
        else:
            lines = ["📋 **최근 지점 이동(Traspasos) 전표 현황 (최근 5건)**\n"]
            for tr in transfers:
                docstatus = tr.get("docstatus", 0)
                status_badge = "✅ 확정(Submit)" if docstatus == 1 else "📝 임시저장(Draft)"
                name = tr.get("name")
                date = tr.get("posting_date")
                from_wh = tr.get("from_warehouse") or "지점"
                to_wh = tr.get("to_warehouse") or "지점"
                lines.append(f"• **[{name}]** ({date}) - {status_badge}")
                lines.append(f"  출발: {from_wh} ➔ 도착: {to_wh}\n")
            return "\n".join(lines)

    elif button_id == "BTN_HELP":
        if is_spanish:
            return (
                "📋 **Guía del Asistente ladypolo en WhatsApp**\n\n"
                "• **Existencias:** `021G stock`, `P160 ROJO`\n"
                "• **Búsqueda:** `buscar 025G`, `P-D60`\n"
                "• **Almacenes:** `almacenes`, `sucursales`"
            )
        else:
            return (
                "📋 **ladypolo WhatsApp 비서 사용 안내**\n\n"
                "• **재고 조회:** `021G-AZUL-400 재고`, `P160 빨강 재고`\n"
                "• **품목 검색:** `025G 검색`, `P-D60 찾아줘`\n"
                "• **창고 목록:** `창고 목록`, `지점 보여줘`"
            )
    
    return "¿En qué puedo ayudarte?" if is_spanish else "원하시는 작업을 입력해 주세요."

def try_zero_token_local_bypass(text: str, sender_name: str = "사용자", user_lang: str = "ko") -> Optional[Dict[str, Any]]:
    """
    [Tier 0: 0-Token 로컬 바이패스 (사용자 언어 세션 100% 반영)]
    """
    cleaned = text.strip()
    norm = spoken_numerals_to_digits(cleaned).lower()
    is_spanish = (user_lang == "es")

    # 1. 인사말 및 메뉴 요청
    if norm in ['hola', 'buenas', 'buenos dias', 'buenas tardes', 'buenas noches', 'que tal', 'hola!', 'menu', 'menú', '안녕', '안녕하세요', '하이', '반가워', '안뇽', '대화 가능한가', '대화 가능한가요', '메뉴', '시작']:
        return {"type": "buttons", "payload": get_welcome_buttons_payload(sender_name, is_spanish=is_spanish)}

    # 2. 도움말
    if norm in ['ayuda', 'help', 'comandos', 'instrucciones', '도움말', '명령어', '사용법']:
        if is_spanish:
            return {"type": "text", "content": (
                "📋 **Guía del Asistente ladypolo en WhatsApp**\n\n"
                "• **Existencias:** `021G stock`, `P160 ROJO`, `3331`\n"
                "• **Búsqueda:** `buscar 025G`, `P-D60`\n"
                "• **Almacenes:** `almacenes`, `ver sucursales`"
            )}
        else:
            return {"type": "text", "content": (
                "📋 **ladypolo WhatsApp 비서 사용 안내**\n\n"
                "• **재고 조회:** `021G-AZUL-400 재고`, `P160 빨강 재고`\n"
                "• **품목 검색:** `025G 검색`, `P-D60 찾아줘`\n"
                "• **창고 목록:** `창고 목록`, `지점 보여줘`"
            )}

    # 3. 창고 목록
    if norm in ['almacenes', 'sucursales', 'ver almacenes', 'lista de almacenes', 'almacen', '창고 목록', '창고목록', '지점 목록', '지점목록', '창고', '지점']:
        warehouses = erpnext_tools.get_warehouses()
        if is_spanish:
            if not warehouses:
                return {"type": "text", "content": "No se encontraron almacenes activos."}
            lines = ["🏬 **Lista de Almacenes Activos (ladypolo)**\n"]
            for w in warehouses:
                lines.append(f"• **{w.get('name')}** ({w.get('warehouse_name', '')})")
            return {"type": "text", "content": "\n".join(lines)}
        else:
            if not warehouses:
                return {"type": "text", "content": "현재 등록된 활성 창고 정보가 없습니다."}
            lines = ["🏬 **ladypolo 활성 창고 목록**\n"]
            for w in warehouses:
                lines.append(f"• **{w.get('name')}** ({w.get('warehouse_name', '')})")
            return {"type": "text", "content": "\n".join(lines)}

    # 4. 품목 코드/색상 기반 즉시 재고 조회
    has_stock_query = any(k in norm for k in ['재고', 'stock', 'existencia', 'cuanto', 'cuánto', 'cuantos', 'cuantas', '몇개', '몇 개', 'hay'])
    
    # 순수 품목코드(예: 'P-160-ROJO-400', '021G-AZUL-400')만 입력된 경우도 재고 조회로 처리
    is_pure_item_code = re.match(r'^[A-Za-z0-9]+-[A-Za-z0-9\-]+$', cleaned) is not None

    if has_stock_query or is_pure_item_code:
        tokens = spoken_numerals_to_digits(cleaned).replace('?', '').replace('!', '').split()
        code_hint = ""
        color_hint = ""
        
        for t in tokens:
            t_upper = t.upper().strip()
            for k_alias, std_val in COLOR_ALIASES.items():
                if k_alias.upper() == t_upper or std_val == t_upper:
                    color_hint = std_val
                    break
            clean_t = re.sub(r'[^A-Z0-9\-]', '', t_upper)
            if clean_t and clean_t not in COLOR_ALIASES.values():
                if re.search(r'\d+', clean_t) or len(clean_t) >= 3:
                    if not any(stop in clean_t for stop in ['재고', 'STOCK', 'EXISTENCIA', 'CUANTO', 'CUANTAS', 'CUANTOS', '몇개']):
                        code_hint = clean_t

        if code_hint:
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
                
                res_lines = []
                for it in items[:3]:
                    st = erpnext_tools.get_item_stock(it['name'])
                    if st.get('success'):
                        tot_qty = int(st['total_qty'])
                        pack = st.get('pack_qty', 1)
                        boxes = st.get('total_boxes', 0)
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
                    return {"type": "text", "content": "\n".join(res_lines).strip()}

    return None
