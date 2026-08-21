import re
from typing import Optional, Tuple, Dict, Any, List
import erpnext_tools

# 1. 색상 별칭 사전 (스페인어/한국어/영어 통합 확장)
COLOR_ALIASES = {
    '네그로': 'NEGRO', 'negro': 'NEGRO', '검정': 'NEGRO', '검정색': 'NEGRO', '블랙': 'NEGRO', 'black': 'NEGRO',
    '베이지': 'BEIGE', 'beige': 'BEIGE',
    '블랑코': 'BLANCO', 'blanco': 'BLANCO', '화이트': 'BLANCO', '하얀': 'BLANCO', '흰색': 'BLANCO', 'white': 'BLANCO',
    '로호': 'ROJO', 'rojo': 'ROJO', '빨강': 'ROJO', '빨간색': 'ROJO', 'red': 'ROJO',
    '아술': 'AZUL', 'azul': 'AZUL', '파랑': 'AZUL', '파란색': 'AZUL', 'blue': 'AZUL',
    '마리노': 'MARINO', 'marino': 'MARINO', '곤색': 'MARINO', '남색': 'MARINO', 'navy': 'MARINO',
    '수르티도': 'SURTIDO', 'surtido': 'SURTIDO', '혼합': 'SURTIDO',
    '우바': 'UVA', 'uva': 'UVA', '보라': 'UVA', '보라색': 'UVA', 'purple': 'UVA', 'morado': 'UVA',
    '비노': 'VINO', 'vino': 'VINO', '와인': 'VINO', '버건디': 'VINO',
    '피우샤': 'FIUSHA', 'fiusha': 'FIUSHA', 'fucsia': 'FIUSHA', '핫핑크': 'FIUSHA',
    '하데': 'JADE', 'jade': 'JADE', '옥색': 'JADE', '민트': 'JADE',
    '모스타사': 'MOSTAZA', 'mostaza': 'MOSTAZA', '겨자': 'MOSTAZA', '머스타드': 'MOSTAZA',
    '그리스': 'GRIS', 'gris': 'GRIS', '회색': 'GRIS', 'gray': 'GRIS',
    '카페': 'CAFE', 'cafe': 'CAFE', 'café': 'CAFE', '갈색': 'CAFE', 'brown': 'CAFE',
    '투르케사': 'TURQUESA', 'turquesa': 'TURQUESA', 'turqueza': 'TURQUESA', '청록': 'TURQUESA',
    '팔로로사': 'PALOROSA', 'palorosa': 'PALOROSA', 'palo rosa': 'PALOROSA', '인디핑크': 'PALOROSA',
    '밀리타르': 'MILITAR', 'militar': 'MILITAR', '카키': 'MILITAR', '국방색': 'MILITAR'
}

# 2. 한글 수사 -> 아라비아 숫자 변환 딕셔너리
KO_DIGITS = {
    '영': 0, '공': 0, '일': 1, '한': 1, '하나': 1, '이': 2, '두': 2, '둘': 2,
    '삼': 3, '세': 3, '셋': 3, '사': 4, '네': 4, '넷': 4, '오': 5, '다섯': 5,
    '육': 6, '여섯': 6, '칠': 7, '일곱': 7, '팔': 8, '여덟': 8, '구': 9, '아홉': 9
}

USER_LANG_CACHE: Dict[str, str] = {}

SPANISH_SIGNALS = [
    'hola', 'buenas', 'dias', 'tardes', 'noches', 'almacen', 'almacenes',
    'stock', 'existencia', 'existencias', 'cuanto', 'cuanta', 'cuantos', 'cuantas',
    'hay', 'precio', 'precios', 'de', 'en', 'por favor', 'gracias', 'ayuda',
    'buscar', 'traspaso', 'traspasos', 'sucursal', 'sucursales', 'caja', 'cajas',
    'pieza', 'piezas', 'bulto', 'bultos', 'quisiera', 'saber', 'disponibilidad'
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
    clean_p = re.sub(r'[^0-9]', '', str(phone or ''))
    raw_lower = text.lower()

    if re.search(r'[가-힣]', text):
        USER_LANG_CACHE[clean_p] = 'ko'
        return 'ko'

    if any(sig in raw_lower for sig in SPANISH_SIGNALS):
        USER_LANG_CACHE[clean_p] = 'es'
        return 'es'

    if clean_p in USER_LANG_CACHE:
        return USER_LANG_CACHE[clean_p]

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
    is_spanish = (user_lang == "es")

    if button_id == "BTN_STOCK":
        if is_spanish:
            return (
                "📦 **Consulta de Inventario**\n\n"
                "Por favor, ingresa el **código y color** que deseas consultar.\n"
                "• Ejemplos: `P-160 UVA`, `021G AZUL`"
            )
        else:
            return (
                "📦 **재고 조회 안내**\n\n"
                "조회하고 싶으신 **품목 코드와 색상**을 입력해 주세요!\n"
                "• 예시: `P160 빨강`, `021G 파랑`"
            )

    elif button_id == "BTN_TRANSFERS":
        transfers = erpnext_tools.get_recent_stock_transfers(limit=5)
        if not transfers:
            return "No se encontraron traspasos recientes." if is_spanish else "📋 최근 등록된 지점 이동 전표가 없습니다."
        
        if is_spanish:
            lines = ["📋 **Traspasos Recientes (Últimos 5)**\n"]
            for tr in transfers:
                docstatus = tr.get("docstatus", 0)
                status_badge = "✅ Confirmado (Submit)" if docstatus == 1 else "📝 Borrador (Draft)"
                lines.append(f"• **[{tr.get('name')}]** ({tr.get('posting_date')}) - {status_badge}")
                lines.append(f"  Origen: {tr.get('from_warehouse') or 'Bodega'} ➔ Destino: {tr.get('to_warehouse') or 'Bodega'}\n")
            return "\n".join(lines)
        else:
            lines = ["📋 **최근 지점 이동 전표 현황 (최근 5건)**\n"]
            for tr in transfers:
                docstatus = tr.get("docstatus", 0)
                status_badge = "✅ 확정(Submit)" if docstatus == 1 else "📝 임시저장(Draft)"
                lines.append(f"• **[{tr.get('name')}]** ({tr.get('posting_date')}) - {status_badge}")
                lines.append(f"  출발: {tr.get('from_warehouse') or '지점'} ➔ 도착: {tr.get('to_warehouse') or '지점'}\n")
            return "\n".join(lines)

    elif button_id == "BTN_HELP":
        if is_spanish:
            return (
                "📋 **Guía del Asistente ladypolo en WhatsApp**\n\n"
                "• **Existencias:** `P-160 UVA`, `stock de 021G-AZUL`\n"
                "• **Almacenes:** `almacenes`\n"
                "• **Precios:** `precio de P-160`"
            )
        else:
            return (
                "📋 **ladypolo WhatsApp 비서 사용 안내**\n\n"
                "• **재고 조회:** `P-160 빨강 재고`, `021G 파랑`\n"
                "• **창고 목록:** `창고 목록`\n"
                "• **단가 확인:** `021G 가격`"
            )
    
    return "¿En qué puedo ayudarte?" if is_spanish else "원하시는 작업을 입력해 주세요."

def try_zero_token_local_bypass(text: str, sender_name: str = "사용자", user_lang: str = "ko") -> Optional[Dict[str, Any]]:
    """
    [Tier 0: 0-Token 로컬 바이패스 - 요청한 특정 품목/컬러만 간결하게 수량 즉답]
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
                "📋 **Guía del Asistente ladypolo**\n\n"
                "• Consulta directamente: `P-160 UVA`, `stock de 021G AZUL`\n"
                "• Ver bodegas: `almacenes`"
            )}
        else:
            return {"type": "text", "content": (
                "📋 **ladypolo WhatsApp 비서 사용 안내**\n\n"
                "• 재고 조회: `P-160 빨강`, `021G 파랑 재고`\n"
                "• 창고 목록: `창고 목록`"
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

    # 4. 품목 코드 + 색상 매칭 재고 조회 (오직 매칭된 1개 품목만 단답형으로 수량 표기)
    has_stock_query = any(k in norm for k in ['재고', 'stock', 'existencia', 'existencias', 'cuanto', 'cuánto', 'cuantos', 'cuantas', 'bulto', 'bultos', 'caja', 'cajas', 'hay', 'disponibilidad', 'saber', '몇개', '몇 개'])
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
                    if not any(stop in clean_t for stop in ['재고', 'STOCK', 'EXISTENCIA', 'CUANTO', 'CUANTAS', 'CUANTOS', 'BULTO', 'BULTOS', 'CAJA', 'CAJAS', 'DISPONIBILIDAD']):
                        code_hint = clean_t

        if code_hint:
            search_queries = [code_hint]
            if re.match(r'^[A-Z]\d+', code_hint):
                search_queries.append(f"{code_hint[0]}-{code_hint[1:]}")
            
            items = []
            for sq in search_queries:
                items = erpnext_tools.search_items(sq, limit=15)
                if items:
                    break

            if items:
                # 특정 색상이 지정된 경우 그 색상만 정확히 필터링 (다른 색상 절대 나열 금지)
                if color_hint:
                    matched_items = [i for i in items if color_hint in i['name'].upper()]
                    if matched_items:
                        items = matched_items
                    else:
                        # 해당 색상이 없는 경우
                        if is_spanish:
                            return {"type": "text", "content": f"❌ No hay existencias disponibles del modelo **{code_hint}** en color **{color_hint}** (0 cajas)."}
                        else:
                            return {"type": "text", "content": f"❌ **{code_hint} {color_hint}** 색상은 현재 보유 중인 재고가 없습니다 (0박스)."}

                # 요청한 품목만 1~2건 간결하게 수량 출력
                res_lines = []
                for it in items[:2]:
                    st = erpnext_tools.get_item_stock(it['name'])
                    if st.get('success'):
                        tot_qty = int(st['total_qty'])
                        pack = st.get('pack_qty', 1)
                        boxes = st.get('total_boxes', 0)
                        wh_list = st.get('warehouses', [])
                        
                        if is_spanish:
                            res_lines.append(f"📦 **[{it['name']}]**")
                            res_lines.append(f"• **Existencia Total:** **{boxes} bultos/cajas** ({tot_qty:,} piezas)")
                            res_lines.append(f"• *Empaque: {pack} pzs por caja*")
                            wh_active = [w for w in wh_list if w.get('actual_qty', 0) > 0]
                            if wh_active:
                                for w in wh_active:
                                    res_lines.append(f"  📍 {w.get('warehouse')}: **{w.get('boxes')} cajas** ({int(w.get('actual_qty')):,} pzs)")
                            else:
                                res_lines.append("  📍 Sin existencias en bodegas.")
                        else:
                            res_lines.append(f"📦 **[{it['name']}]**")
                            res_lines.append(f"• **총 재고량:** **{boxes}박스** ({tot_qty:,}개)")
                            res_lines.append(f"• *입수량: 박스당 {pack}개*")
                            wh_active = [w for w in wh_list if w.get('actual_qty', 0) > 0]
                            if wh_active:
                                for w in wh_active:
                                    res_lines.append(f"  📍 {w.get('warehouse')}: **{w.get('boxes')}박스** ({int(w.get('actual_qty')):,}개)")
                            else:
                                res_lines.append("  📍 현재 보유 중인 지점 재고가 없습니다.")
                        res_lines.append("")

                if res_lines:
                    return {"type": "text", "content": "\n".join(res_lines).strip()}

    return None
