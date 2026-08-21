import os
import sys
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

import erpnext_tools

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PRIMARY_MODEL = "gemini-3.6-flash"
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]

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

def run_agent(user_message: str, sender_name: str = "사용자") -> str:
    """
    사용자의 WhatsApp 메시지를 받아 Gemini 에이전트를 실행하고 최종 답변을 생성합니다.
    """
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

    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS
    last_error = None

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                chat = client.chats.create(model=model_name, config=config)
                response = chat.send_message(user_message)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = e
                print(f"⚠️ 모델 [{model_name}] 시도 {attempt+1} 실패: {e}")
                time.sleep(1)

    return f"죄송합니다, {sender_name}님. 일시적인 서비스 지연으로 요청을 처리하지 못했습니다: {last_error}"

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 KTK WMS AI 에이전트 재시도/안정화 테스트")
    print("=" * 60)
    
    q = "021G-AZUL-400 재고 어디에 몇 개 있어?"
    print(f"👤 [질문]: {q}")
    reply = run_agent(q, "대표님")
    print(f"🤖 [AI 에이전트 답변]:\n{reply}")
