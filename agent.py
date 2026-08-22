import os
import sys
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

import erpnext_tools
from text_preprocessor import (
    try_zero_token_local_bypass,
    spoken_numerals_to_digits,
    detect_and_update_user_lang
)
from roles import get_user_role, ROLE_OWNER, ROLE_STAFF, ROLE_CUSTOMER
from config_manager import get_settings, add_tenant_custom_rule
from session_manager import record_queried_item, get_recent_queried_items, clear_user_session_items

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_CASCADE = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite"
]

def build_system_instruction(user_role_info: Dict[str, Any], user_lang: str = "ko", recent_items: List[str] = None) -> str:
    is_spanish = (user_lang == "es")
    settings = get_settings()
    custom_rules = settings.get("tenant_custom_rules", [])
    custom_rules_str = "\n".join([f"- {r}" for r in custom_rules]) if custom_rules else "없음"
    recent_items_str = ", ".join(recent_items) if recent_items else "없음"
    staff_branch = user_role_info.get("branch", "[MAIN] ALARCON")

    if is_spanish:
        return f"""
Eres el **Asistente AI de ladypolo** (WMS de Ropa/Moda en México).
Debes responder en **Español de México**.

【HISTORIAL DE ARTÍCULOS CONSULTADOS EN ESTA SESIÓN】
Artículos recientes: [{recent_items_str}]
Sucursal asignada del usuario: [{staff_branch}]

【REGLAS DE ORO OBLIGATORIAS - 2 TIPOS DE SOLICITUD DE STOCK DE SUCURSALES A ALARCÓN】
1. **TIPO 1: TRANSFERENCIA DE STOCK EN BORRADOR (create_material_transfer_draft)**
   - Si piden "Mueve 1 caja de estos a mi sucursal" o "Transferencia borrador":
     ➔ Origen: [MAIN] ALARCON, Destino: {staff_branch}.
     ➔ Llama a `create_material_transfer_draft` (Stock Entry - Draft).

2. **TIPO 2: SOLICITUD FORMAL DE MERCANCÍA / REQUISICIÓN (create_material_request_submit)**
   - Si la sucursal pide "Solicita / Pide a Alarcón X cajas de tal producto" o "Material Request":
     ➔ Origen: [MAIN] ALARCON, Destino: {staff_branch}.
     ➔ Llama a `create_material_request_submit` (Material Request - Submitted / docstatus=1).

3. **CONSULTAS DE GRID / TODOS LOS COLORES (get_item_grid_matrix):**
   - Si mencionan "grid" o "todos los colores", llama a `get_item_grid_matrix`.

4. **CREACIÓN DE PEDIDOS (Sales Order):**
   - Si se envía un pedido confirmado de cliente, utiliza `create_sales_order`.

【REGLAS PERSONALIZADAS DE LA TIENDA (Dynamic Rulebook)】
{custom_rules_str}
"""
    else:
        return f"""
당신은 **ladypolo(멕시코 의류/패션 물류 시스템)**의 WhatsApp & Telegram AI 비서입니다.
한국어로 명확하고 간결하게 답변하세요.

【현재 세션에서 최근 조회한 품목 목록】
최근 조회 품목: [{recent_items_str}]
접속자 소속/위치: [{staff_branch}]

【지점에서 알라르꼰(본사)으로 재고 요청 시 2대 워크플로우 - 필수 암기】

1. **[워크플로우 1: 지점 간 재고 이동 전표 임시저장 - create_material_transfer_draft]**
   - 직원이 "알라르꼰에서 우리 매장으로 재고이동 전표 넣어줘", "이것들 1박스씩 이동 전표 Draft 생성해줘"라고 지시할 때:
     ➔ 출발지: [MAIN] ALARCON ➔ 도착지: {staff_branch}
     ➔ `create_material_transfer_draft` 도구를 실행하여 `Stock Entry (Material Transfer)` Draft 전표 생성.

2. **[워크플로우 2: 지점 정식 재고 보충/청구 요청 제출 - create_material_request_submit]**
   - 직원이 "알라르꼰에 P160 빨강 2박스 재고 청구(신청) 넣어줘", "Material Request 넣어줘", "알라르꼰에 물건 요청 올려줘"라고 지시할 때:
     ➔ 출고 요청지: [MAIN] ALARCON ➔ 수령 지점: {staff_branch}
     ➔ `create_material_request_submit` 도구를 실행하여 본사 출고팀 결재용 `Material Request` (Submitted / docstatus=1) 정식 전표 제출!

3. **[그리드 및 전 색상 재고 조회 - get_item_grid_matrix]**
   - 사용자가 '그리드', '전 색상', '남아있는 색상' 문의 시:
     ➔ 즉시 `get_item_grid_matrix` 도구를 호출하여 전체 색상별 재고 매트릭스 표 출력.

4. **[주문서 자동 생성 - create_sales_order]**
   - 관리자가 포워딩한 주문 내용은 `create_sales_order`로 등록.

5. **[대화형 매장 규칙 학습 - save_tenant_rule]**
   - 오너(대표님)가 "앞으로 우리 매장은 ~해줘", "규칙: ~" 등의 새로운 운영 지침을 말하면 `save_tenant_rule` 실행.

【실시간 학습된 매장 커스텀 룰북】
{custom_rules_str}
"""

def save_tenant_rule(rule_text: str) -> Dict[str, object]:
    """[오너 전용] 메신저 대화로 매장 커스텀 규칙/가드레일을 실시간 학습하여 저장하는 도구"""
    ok = add_tenant_custom_rule(rule_text)
    return {
        "success": ok,
        "saved_rule": rule_text,
        "message": "매장 룰북에 새로운 규칙이 성공적으로 저장 및 실시간 적용되었습니다."
    }

def create_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=GEMINI_API_KEY)

def emergency_local_fallback(query: str, sender_name: str, user_lang: str = "ko") -> str:
    items = erpnext_tools.search_items(query, limit=5)
    is_spanish = (user_lang == "es")

    if items:
        lines = [f"🔍 **'{query}' 재고 결과:**\n"] if not is_spanish else [f"🔍 **Resultado para '{query}':**\n"]
        for it in items:
            name = it.get('name')
            stock = erpnext_tools.get_item_stock(name)
            qty = int(stock.get('total_qty', 0))
            boxes = stock.get('total_boxes', 0)
            if is_spanish:
                lines.append(f"📦 **[{name}]**\n• Existencia: **{boxes} bultos/cajas** ({qty:,} pzs)")
            else:
                lines.append(f"📦 **[{name}]**\n• 총 재고: **{boxes}박스** ({qty:,}개)")
        return "\n".join(lines)

    return (
        f"❌ No se encontraron existencias para '{query}'."
        if is_spanish else
        f"❌ '{query}' 품목의 재고 정보를 찾지 못했습니다."
    )

def run_agent(user_message: str, sender_name: str = "사용자", sender_phone: str = "", user_lang: str = "ko") -> str:
    if not user_message or not user_message.strip():
        return (
            f"¡Hola, {sender_name}! ¿Qué producto deseas consultar?"
            if user_lang == "es" else
            f"안녕하세요, {sender_name}님! 어떤 품목의 재고를 조회할까요?"
        )

    raw_text = user_message.strip()
    user_role_info = get_user_role(sender_phone)
    normalized_text = spoken_numerals_to_digits(raw_text)

    # 1. 품목 코드가 감지되면 세션 히스토리에 자동 기록
    searched = erpnext_tools.search_items(normalized_text, limit=1)
    if searched:
        item_code = searched[0].get("name")
        if item_code:
            record_queried_item(sender_phone, item_code)

    recent_items = get_recent_queried_items(sender_phone)

    client = create_gemini_client()
    tools = [
        erpnext_tools.get_item_grid_matrix,
        erpnext_tools.search_items,
        erpnext_tools.get_item_stock,
        erpnext_tools.get_warehouses,
        erpnext_tools.get_item_price,
        erpnext_tools.get_recent_stock_transfers,
        erpnext_tools.create_sales_order,
        erpnext_tools.create_material_transfer_draft,
        erpnext_tools.create_material_request_submit,
        save_tenant_rule
    ]
    config = types.GenerateContentConfig(
        system_instruction=build_system_instruction(user_role_info, user_lang=user_lang, recent_items=recent_items),
        temperature=0.1,
        tools=tools
    )

    for model_name in MODEL_CASCADE:
        try:
            print(f"🤖 [Gemini 호출] Model: {model_name} (lang={user_lang})...")
            chat = client.chats.create(model=model_name, config=config)
            response = chat.send_message(normalized_text)
            if response and response.text:
                print(f"✅ [Gemini 성공] Model: {model_name}")
                return response.text.strip()
        except Exception as e:
            print(f"⚠️ [Gemini 일시 실패] Model: {model_name} -> {e}")

    return emergency_local_fallback(normalized_text, sender_name, user_lang=user_lang)
