import os
import sys
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

import erpnext_tools
from text_preprocessor import try_zero_token_local_bypass, spoken_numerals_to_digits

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 안정성과 속도(1.5초)가 뛰어난 모델 순서
MODEL_CASCADE = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite"
]

SYSTEM_INSTRUCTION = """
당신은 KTK WMS(멕시코 의류/패션 물류 및 재고 관리 시스템)의 WhatsApp 전용 AI 비서입니다.
현장 관리자 및 직원들이 모바일 WhatsApp을 통해 재고, 품목, 단가, 지점 현황을 물어보면 제공된 도구(Tools)를 활용하여 실시간 ERPNext 데이터를 조회하고 정확하게 답변하세요.

[핵심 행동 수칙]
1. 언어 대응:
   - 사용자가 한국어로 질문하면 한국어로 친절하고 명확하게 답변합니다.
   - 사용자가 스페인어로 질문하면 자연스러운 멕시코 비즈니스 스페인어(Español)로 답변합니다.
2. 수량 표기 원칙:
   - 재고를 안내할 때는 총 수량(낱개)뿐만 아니라 **박스(Cajas/Box)** 수량과 **잔여 낱개(Pzs/Eaches)**를 함께 알기 쉽게 표기합니다.
   - 예: "📦 [MAIN] ALARCON: 4박스 (총 1,600개)"
3. WhatsApp 모바일 최적화 포맷:
   - 불필요하게 긴 설명은 피하고, 핵심 정보 위주로 이모지와 불릿 포인트를 활용하여 한눈에 들어오게 정리합니다.
4. 모호한 품목명 처리:
   - 사용자가 품목명을 일부만 말한 경우(예: "021G 재고 알려줘"), 먼저 `search_items`로 품목 목록을 찾고 연관된 품목들의 재고를 조회하여 안내합니다.
5. 데이터 부재 시:
   - 검색 결과가 없거나 재고가 0인 경우, 솔직하고 명확하게 안내합니다.
"""

def create_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=GEMINI_API_KEY)

def emergency_local_fallback(query: str, sender_name: str) -> str:
    """
    [AI 지연/장애 시 긴급 알림 및 로컬 즉시 검색 폴백]
    Gemini API 장애 발생 시 사용자에게 AI 지연 알림을 명확히 전달하고,
    ERPNext 로컬 직접 검색 결과를 대신 제공합니다.
    """
    print(f"🚨 [AI 접속 지연/장애 감지 ➔ 긴급 알림 및 로컬 폴백 발동] Query: '{query}'")
    
    # 1. 로컬 품목 검색 시도
    items = erpnext_tools.search_items(query, limit=5)
    if items:
        lines = [
            f"⚠️ **[안내] AI 서버 응답이 지연되어 기본 시스템 검색으로 즉시 안내해 드립니다.** ({sender_name}님)\n",
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
            
            # 창고별 세부
            wh_list = [w for w in stock.get('warehouses', []) if w.get('actual_qty', 0) > 0]
            for w in wh_list:
                lines.append(f"  📍 {w.get('warehouse')}: {w.get('boxes')}박스 ({int(w.get('actual_qty')):,}개)")
        return "\n".join(lines)

    # 검색 결과조차 없는 경우
    return (
        f"⚠️ **[시스템 알림]**\n"
        f"현재 Google AI 서비스 응답이 일시적으로 지연되고 있습니다.\n"
        f"입력하신 **'{query}'**에 해당하는 품목 코드를 찾지 못했으니, 정확한 품목명(예: `021G`, `P-160`)을 입력해 주세요!"
    )

def run_agent(user_message: str, sender_name: str = "사용자") -> str:
    """[통합 AI 에이전트 실행 파이프라인]"""
    if not user_message or not user_message.strip():
        return f"안녕하세요, {sender_name}님! 무엇을 도와드릴까요?"

    raw_text = user_message.strip()

    # 1. [Tier 0] 0-Token 로컬 바이패스 (0.1초 즉답)
    local_reply = try_zero_token_local_bypass(raw_text, sender_name)
    if local_reply:
        print(f"⚡ [0-Token Local Bypass] '{raw_text}' -> 즉시 로컬 응답")
        return local_reply

    # 2. 텍스트 전처리 (수사/색상 정규화)
    normalized_text = spoken_numerals_to_digits(raw_text)

    # 3. Gemini 고속 Flash 모델 Cascade
    client = create_gemini_client()
    tools = [
        erpnext_tools.search_items,
        erpnext_tools.get_item_stock,
        erpnext_tools.get_warehouses,
        erpnext_tools.get_item_price
    ]
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2,
        tools=tools
    )

    for model_name in MODEL_CASCADE:
        try:
            print(f"🤖 [Gemini 호출] Model: {model_name}...")
            chat = client.chats.create(model=model_name, config=config)
            response = chat.send_message(normalized_text)
            if response and response.text:
                print(f"✅ [Gemini 성공] Model: {model_name}")
                return response.text.strip()
        except Exception as e:
            print(f"⚠️ [Gemini 일시 실패] Model: {model_name} -> {e}")

    # 4. [Tier 4] AI 전체 장애 시 긴급 알림 + 로컬 검색 즉시 회신
    return emergency_local_fallback(normalized_text, sender_name)
