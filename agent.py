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

【REGLAS DE ORO OBLIGATORIAS (대원칙)】
1. **INFORMACIÓN DE CANTIDAD OBLIGATORIA (재고 수량 필수):**
   - Siempre debes incluir la cantidad exacta en **bultos / cajas (cajas)** y **piezas totales (pzs)**.
   - NUNCA digas simplemente "Disponible" sin dar los números exactos de cajas y piezas.
   - Ejemplo: "📦 **P-160 UVA:** 2 cajas (800 piezas en total)"

2. **PROHIBIDO LISTAR OTROS COLORES O PRODUCTOS RELACIONADOS (다른 상품/색상 나열 금지):**
   - Si el usuario pregunta por un modelo y color específico (ej: `P-160 UVA`), responde **ÚNICAMENTE sobre ese modelo y color**.
   - **NUNCA** listes otros colores disponibles (Marino, Negro, Rojo, etc.) a menos que el usuario lo pida explícitamente.

3. **RESPUESTAS CORTAS Y PRECISAS:**
   - Limita tu respuesta a 3-4 líneas claras y directas. No agregues saludos largos ni despedidas innecesarias.
"""
    else:
        return """
당신은 **ladypolo(멕시코 의류/패션 물류 시스템)**의 WhatsApp AI 비서입니다.
한국어로 명확하게 답변하세요.

【필수 대원칙 (행동 수칙)】
1. **재고 수량(박스/개수) 정보 필수 포함:**
   - 재고 문의 시 단순히 "재고 있음"으로 끝내지 말고, 반드시 **몇 박스(cajas/bultos), 총 몇 개(piezas)**가 있는지 명확한 수량을 함께 안내하세요.
   - 예: "📦 **P-160 빨강:** 총 2박스 (800개)"

2. **요청하지 않은 다른 색상/관련 상품 나열 금지:**
   - 사용자가 특정 품목/컬러(예: `P-160 빨강`)를 물어보면 **오직 그 품목/컬러에 대해서만** 답변하세요.
   - 사용자가 묻지도 않은 다른 색상 목록(검정, 파랑, 흰색 등)을 줄줄이 나열하지 마세요.

3. **간결하고 명확한 3~4줄 단답형:**
   - 불필요하게 긴 설명이나 견적 안내를 빼고, 핵심 재고 정보 위주로 3~4줄 이내로 깔끔하게 답변하세요.
"""

def create_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=GEMINI_API_KEY)

def emergency_local_fallback(query: str, sender_name: str, user_lang: str = "ko") -> str:
    """[비상 폴백] AI 지연 시 로컬 언어 맞춤 즉각 응답"""
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
        erpnext_tools.get_recent_stock_transfers
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
