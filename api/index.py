import os
import sys
import time

# 프로젝트 루트 디렉토리를 Python Path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

from whatsapp_client import send_whatsapp_message, parse_incoming_message, get_account_status
from agent import run_agent

app = FastAPI(title="KTK WMS WhatsApp Agent on Vercel")

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ktk_wms_webhook_secret_2026")

# 중복 응답 방지를 위한 Message ID 캐시 (최근 1000건)
PROCESSED_MESSAGE_IDS = set()
MAX_CACHE_SIZE = 1000

@app.api_route("/{full_path:path}", methods=["GET", "POST"])
async def catch_all_handler(request: Request, full_path: str = ""):
    global PROCESSED_MESSAGE_IDS
    method = request.method
    query_params = request.query_params

    # 1. Meta Webhook Verification (GET 요청)
    if method == "GET":
        mode = query_params.get("hub.mode")
        token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        if mode or token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                return PlainTextResponse(content=str(challenge), status_code=200)
            else:
                raise HTTPException(status_code=403, detail="Verification token mismatch")

        # 일반 GET 요청 시 헬스체크 반환
        account_info = get_account_status()
        return JSONResponse(content={
            "status": "healthy",
            "service": "KTK WMS WhatsApp AI Agent",
            "platform": "Vercel Serverless",
            "whatsapp_account": account_info
        }, status_code=200)

    # 2. WhatsApp 실시간 메시지 수신 (POST 요청)
    elif method == "POST":
        try:
            body = await request.json()
        except Exception as e:
            print(f"❌ JSON 파싱 실패: {e}")
            return JSONResponse(content={"status": "invalid json"}, status_code=400)

        # 메시지 정보 파싱
        msg_info = parse_incoming_message(body)
        
        if msg_info:
            message_id = msg_info.get("message_id")
            sender_phone = msg_info.get("sender_phone")
            sender_name = msg_info.get("sender_name")
            text = msg_info.get("text")

            # [중복 방지 필터] 이미 처리한 메시지 ID인 경우 무시
            if message_id:
                if message_id in PROCESSED_MESSAGE_IDS:
                    print(f"⏩ [중복 메시지 스킵] message_id={message_id}")
                    return Response(content="EVENT_RECEIVED", status_code=200)
                
                # 캐시 관리
                PROCESSED_MESSAGE_IDS.add(message_id)
                if len(PROCESSED_MESSAGE_IDS) > MAX_CACHE_SIZE:
                    PROCESSED_MESSAGE_IDS.pop()

            if text and sender_phone:
                print(f"\n📩 [WhatsApp 수신] {sender_name}({sender_phone}): '{text}'")
                try:
                    # AI 에이전트 실행 및 회신 발송
                    ai_reply = run_agent(user_message=text, sender_name=sender_name)
                    print(f"🤖 [AI 답변]\n{ai_reply}")
                    res = send_whatsapp_message(sender_phone, ai_reply)
                    print(f"📨 [WhatsApp 발송 완료]: {res}")
                except Exception as agent_err:
                    print(f"❌ 에이전트 오류: {agent_err}")
                    send_whatsapp_message(sender_phone, f"죄송합니다, {sender_name}님. 요청을 처리하는 중 일시적인 오류가 발생했습니다.")

        return Response(content="EVENT_RECEIVED", status_code=200)

    return Response(content="Method Not Allowed", status_code=405)
