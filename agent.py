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
    role = user_role_info.get("role", ROLE_CUSTOMER)
    is_spanish = (user_lang == "es")

    lang_instruction = (
        "【중요: 언어 강제 규칙】\n"
        "이 사용자는 [스페인어(Español)] 사용자입니다. 어떤 경우에도 한국어를 섞지 말고, 100% 자연스러운 멕시코 비즈니스 스페인어(Español de México)로만 답변하세요!"
        if is_spanish else
        "【중요: 언어 강제 규칙】\n"
        "이 사용자는 [한국어] 사용자입니다. 친절하고 정확한 한국어로 답변하세요."
    )

    if is_spanish:
        role_guideline = (
            "El usuario es [Administrador/Dueño]. Proporciona detalles completos de existencias, precios y traspasos de todos los almacenes."
            if role == ROLE_OWNER else
            "El usuario es [Empleado de Sucursal]. Proporciona existencias disponibles en bodega principal (ALARCON) y sucursales."
            if role == ROLE_STAFF else
            "El usuario es [Cliente General]. NO reveles nombres de almacenes internos ni inventario exacto. Solo indica si hay disponibilidad (Disponible/Agotado) y opciones de color/precio."
        )
    else:
        role_guideline = (
            "현재 대화 상대는 [오너/최고관리자]입니다. 모든 지점/창고의 상세 재고, 원가 및 단가, 전표 현황 등 모든 정보를 상세하게 제공하세요."
            if role == ROLE_OWNER else
            "현재 대화 상대는 [직원]입니다. 본사(ALARCON) 및 지점의 실시간 가용 재고, 기본 판매 단가, 이동 전표 관련 정보를 제공하세요."
            if role == ROLE_STAFF else
            "현재 대화 상대는 [일반 고객]입니다. 내부 창고명이나 정확한 내부 총수량은 비공개로 유지하고, 단순히 구매 가능 여부(있음/품절)와 컬러/소비자가 위주로 안내하세요."
        )

    return f"""
당신은 **ladypolo(멕시코 의류/패션 물류 및 재고 관리 시스템)**의 WhatsApp 전용 AI 비서입니다.

{lang_instruction}

[접속자 역할 및 보안 수칙]
{role_guideline}

[핵심 행동 수칙]
1. 정체성:
   - 당신의 이름/브랜드는 **ladypolo 비서** (스페인어: **Asistente de ladypolo**)입니다.
2. 엄격한 업무 범위 (토큰 절약 가드레일):
   - 당신은 **오직 ladypolo 재고, 품목, 창고, 단가, 전표 등 물류 업무만** 수행합니다.
   - 날씨, 번역, 일반 상식, 코딩, 일상 잡담 등 물류와 무관한 질문은 단호하고 정중하게 거절하세요.
     (스페인어: "Disculpa, solo puedo ayudarte con temas de inventario y logística de ladypolo.")
3. 수량 표기:
   - 총 낱개 수량과 함께 **박스(Cajas/Box)** 수량을 반드시 알기 쉽게 표기합니다.
"""

def create_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=GEMINI_API_KEY)

def emergency_local_fallback(query: str, sender_name: str, user_lang: str = "ko") -> str:
    """[비상 폴백] AI 지연 시 로컬 언어 맞춤 즉각 응답"""
    print(f"🚨 [Emergency Fallback Triggered] Query: '{query}' (lang={user_lang})")
    items = erpnext_tools.search_items(query, limit=5)
    is_spanish = (user_lang == "es")

    if items:
        if is_spanish:
            lines = [
                f"⚠️ **[Aviso] El servicio de IA está experimentando lentitud. Mostrando resultados directos:**\n",
                f"🔍 **Resultados para '{query}':**"
            ]
            for it in items:
                name = it.get('name')
                stock = erpnext_tools.get_item_stock(name)
                qty = int(stock.get('total_qty', 0))
                boxes = stock.get('total_boxes', 0)
                pack = stock.get('pack_qty', 1)
                lines.append(f"\n📦 **[{name}]**")
                lines.append(f"• Total: **{boxes} cajas** ({qty:,} pzs) *(Empaque: {pack} pzs/caja)*")
            return "\n".join(lines)
        else:
            lines = [
                f"⚠️ **[안내] AI 서버 응답이 지연되어 ladypolo 기본 검색으로 안내해 드립니다.** ({sender_name}님)\n",
                f"🔍 **'{query}' 관련 품목 실시간 재고:**"
            ]
            for it in items:
                name = it.get('name')
                stock = erpnext_tools.get_item_stock(name)
                qty = int(stock.get('total_qty', 0))
                boxes = stock.get('total_boxes', 0)
                pack = stock.get('pack_qty', 1)
                lines.append(f"\n📦 **[{name}]**")
                lines.append(f"• 총 재고: **{boxes}박스** ({qty:,}개) *(입수: {pack}개/box)*")
            return "\n".join(lines)

    return (
        f"⚠️ **[Aviso]** No se encontró el producto '{query}'. Por favor verifica el código (ej: `021G`, `P-160`)."
        if is_spanish else
        f"⚠️ **[ladypolo 알림]** '{query}'에 해당하는 품목을 찾지 못했습니다. 정확한 품목명(예: `021G`, `P-160`)을 입력해 주세요!"
    )

def run_agent(user_message: str, sender_name: str = "사용자", sender_phone: str = "", user_lang: str = "ko") -> str:
    """[역할 및 언어 세션 기반 통합 AI 에이전트 실행]"""
    if not user_message or not user_message.strip():
        return (
            f"¡Hola, {sender_name}! Soy el **Asistente de ladypolo**. ¿En qué puedo ayudarte?"
            if user_lang == "es" else
            f"안녕하세요, {sender_name}님! **ladypolo 비서**입니다. 무엇을 도와드릴까요?"
        )

    raw_text = user_message.strip()
    user_role_info = get_user_role(sender_phone)
    print(f"👤 [User Session] Phone={sender_phone} | Role={user_role_info.get('role_name')} | Lang={user_lang}")

    # 1. 텍스트 전처리
    normalized_text = spoken_numerals_to_digits(raw_text)

    # 2. Gemini 고속 Flash 모델 Cascade
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
        temperature=0.2,
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

    # 3. 비상 로컬 검색 회신
    return emergency_local_fallback(normalized_text, sender_name, user_lang=user_lang)
