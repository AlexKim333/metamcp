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

# 다계층 고가용성 Flash 모델 Fallback 순서
MODEL_CASCADE = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest"
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
    [비상 폴백 (Emergency Fallback)]
    모든 Gemini API가 일시 장애인 경우에도,
    로컬 검색 도구를 직접 실행하여 최소한의 재고/품목 정보를 사용자에게 회신합니다.
    """
    print(f"🚨 [Emergency Fallback Triggered] Query: '{query}'")
    
    # 1. 품목 검색 시도
    items = erpnext_tools.search_items(query, limit=5)
    if items:
        lines = [
            f"ℹ️ (AI 서비스 일시 지연으로 기본 검색 결과로 안내해 드립니다, {sender_name}님)\n",
            f"🔍 **'{query}' 관련 품목 검색 결과 ({len(items)}건):**"
        ]
        for it in items:
            name = it.get('name')
            stock = erpnext_tools.get_item_stock(name)
            qty = stock.get('total_qty', 0)
            boxes = stock.get('total_boxes', 0)
            lines.append(f"• **[{name}]** {it.get('item_name', '')} ➔ 총 재고: {boxes}박스 ({qty:,.0f}개)")
        return "\n".join(lines)

    return f"죄송합니다, {sender_name}님. 현재 AI 서비스 점검 중이며 일치하는 품목을 찾지 못했습니다. 잠시 후 다시 시도해 주세요."

def run_agent(user_message: str, sender_name: str = "사용자") -> str:
    """
    [통합 AI 에이전트 실행 파이프라인]
    1. Tier 0: 0-Token 로컬 바이패스 (인사, 도움말, 정형 재고조회 -> LLM 비용 0원/0.01초 즉시 응답)
    2. 텍스트 전처리: 한글 수사("삼삼삼일") 및 색상("네그로") 정규화
    3. Tier 1~3: Gemini 다중 모델 자동 Fallback (gemini-3.7-flash -> gemini-3.6-flash -> gemini-3.5-flash)
    4. Tier 4: Gemini 전면 장애 시 Emergency Local Search Fallback
    """
    if not user_message or not user_message.strip():
        return f"안녕하세요, {sender_name}님! 무엇을 도와드릴까요?"

    raw_text = user_message.strip()

    # -------------------------------------------------------------
    # 1. [Tier 0] 토큰 0개 로컬 바이패스 (Zero-Token Bypass)
    # -------------------------------------------------------------
    local_reply = try_zero_token_local_bypass(raw_text, sender_name)
    if local_reply:
        print(f"⚡ [0-Token Local Bypass] '{raw_text}' -> 즉시 로컬 응답 (Gemini 미호출)")
        return local_reply

    # -------------------------------------------------------------
    # 2. 텍스트 전처리 (한국어 수사/색상 정규화)
    # -------------------------------------------------------------
    normalized_text = spoken_numerals_to_digits(raw_text)
    if normalized_text != raw_text:
        print(f"🔄 [Text Preprocessed] '{raw_text}' ➔ '{normalized_text}'")

    # -------------------------------------------------------------
    # 3. Gemini 다계층 모델 Fallback & Auto-Retry
    # -------------------------------------------------------------
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

    last_error = None
    for model_name in MODEL_CASCADE:
        try:
            print(f"🤖 [Gemini 호출] Model: {model_name}...")
            chat = client.chats.create(model=model_name, config=config)
            response = chat.send_message(normalized_text)
            if response and response.text:
                print(f"✅ [Gemini 성공] Model: {model_name}")
                return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"⚠️ [Gemini 실패] Model: {model_name} -> {e}")
            time.sleep(0.5)

    # -------------------------------------------------------------
    # 4. [Tier 4] 비상 로컬 검색 폴백 (Emergency Fallback)
    # -------------------------------------------------------------
    return emergency_local_fallback(normalized_text, sender_name)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 [최신 모델 Fallback 검증]")
    print("=" * 60)
    
    q = "021G-NEGRO-400 재고 얼마 있어?"
    ans = run_agent(q, "대표님")
    print(f"답변:\n{ans}")
