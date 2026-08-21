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

def build_system_instruction(user_role_info: Dict[str, Any], user_lang: str = "ko") -> str:
    is_spanish = (user_lang == "es")

    if is_spanish:
        return """
Eres el **Asistente AI de ladypolo** (WMS de Ropa/Moda en México).
Debes responder en **Español de México**.

【REGLAS DE ORO OBLIGATORIAS】
1. **CONSULTAS DE STOCK:**
   - Responde ÚNICAMENTE sobre el modelo y color solicitado.
   - Incluye siempre la cantidad exacta en **cajas / bultos** y **piezas totales**.
   - PROHIBIDO listar otros colores o productos no solicitados.

2. **CREACIÓN DE PEDIDOS (Sales Order):**
   - Si se envía un pedido confirmado (ej: "Carlos: P-160 ROJO 2 cajas a $300, 021G AZUL 3 cajas a $450"):
     ➔ El precio indicado ($300, $450) es el **precio por caja (rate_per_box)**.
     ➔ Utiliza `create_sales_order` para registrar el pedido en ERPNext.
     ➔ Genera un recibo formal con código, cajas, piezas, precio por caja y total.
"""
    else:
        return """
당신은 **ladypolo(멕시코 의류/패션 물류 시스템)**의 WhatsApp AI 비서입니다.
한국어로 명확하게 답변하세요.

【필수 대원칙 (행동 수칙)】
1. **재고 수량(박스/개수) 정보 필수 포함:**
   - 재고 문의 시 요청한 품목/컬러에 대해서만 **몇 박스(cajas/bultos), 총 몇 개(piezas)**가 있는지 명확한 수량을 안내하세요.
   - 요청하지 않은 다른 색상이나 관련 상품을 줄줄이 나열하지 마세요.

2. **주문서 / 견적서 자동 생성 (create_sales_order):**
   - 관리자 또는 지점장이 포워딩한 주문/견적 텍스트를 받으면:
     ➔ 언급된 단가(예: "2박스 단가 300")는 **박스당 단가(rate_per_box)**로 `create_sales_order`를 호출하세요.
     ➔ ERPNext에 등록된 `order_name`(예: SO-2026-xxxxx)과 함께 [고객명, 출고 지점, 품목, 박스수량×입수량=총수량, 박스당 단가, 소계, 총 주문 금액]이 정리된 깔끔한 정식 주문서 영수증을 출력하세요.
"""

def create_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=GEMINI_API_KEY)

def emergency_local_fallback(query: str, sender_name: str, user_lang: str = "ko") -> str:
    print(f"🚨 [Emergency Fallback Triggered] Query: '{query}' (lang={user_lang})")
    items = erpnext_tools.search_items(query, limit=2)
    is_spanish = (user_lang == "es")

    if items:
        if is_spanish:
            lines = [f"🔍 **Resultado para '{query}':**\n"]
            for it in items:
                name = it.get('name')
                stock = erpnext_tools.get_item_stock(name)
                qty = int(stock.get('total_qty', 0))
                boxes = stock.get('total_boxes', 0)
                lines.append(f"📦 **[{name}]**")
                lines.append(f"• Existencia: **{boxes} bultos/cajas** ({qty:,} pzs)")
            return "\n".join(lines)
        else:
            lines = [f"🔍 **'{query}' 재고 결과:**\n"]
            for it in items:
                name = it.get('name')
                stock = erpnext_tools.get_item_stock(name)
                qty = int(stock.get('total_qty', 0))
                boxes = stock.get('total_boxes', 0)
                lines.append(f"📦 **[{name}]**")
                lines.append(f"• 총 재고: **{boxes}박스** ({qty:,}개)")
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

    client = create_gemini_client()
    tools = [
        erpnext_tools.search_items,
        erpnext_tools.get_item_stock,
        erpnext_tools.get_warehouses,
        erpnext_tools.get_item_price,
        erpnext_tools.get_recent_stock_transfers,
        erpnext_tools.create_sales_order
    ]
    config = types.GenerateContentConfig(
        system_instruction=build_system_instruction(user_role_info, user_lang=user_lang),
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
