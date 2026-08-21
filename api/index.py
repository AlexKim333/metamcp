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

app = FastAPI(title="ladypolo WhatsApp Agent on Vercel")

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ktk_wms_webhook_secret_2026")

# 최근 120초 내 유효 메시지만 처리 (Meta의 과거 재전송 패킷 완벽 차단)
MAX_MESSAGE_AGE_SECONDS = 120

@app.api_route("/{full_path:path}", methods=["GET", "POST"])
async def catch_all_handler(request: Request, full_path: str = ""):
    method = request.method
    query_params = request.query_params

    # 1. Meta Webhook Verification (GET)
    if method == "GET":
        mode = query_params.get("hub.mode")
        token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        if mode or token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                return PlainTextResponse(content=str(challenge), status_code=200)
            else:
                raise HTTPException(status_code=403, detail="Verification token mismatch")

        account_info = get_account_status()
        return JSONResponse(content={
            "status": "healthy",
            "service": "ladypolo WhatsApp AI Agent",
            "platform": "Vercel Serverless",
            "whatsapp_account": account_info
        }, status_code=200)

    # 2. WhatsApp 실시간 메시지 수신 (POST)
    elif method == "POST":
        try:
            body = await request.json()
        except Exception as e:
            print(f"❌ JSON 파싱 실패: {e}")
            return JSONResponse(content={"status": "invalid json"}, status_code=400)

        msg_info = parse_incoming_message(body)
        
        if msg_info:
            msg_timestamp = msg_info.get("timestamp", 0)
            now = int(time.time())
            
            # [과거 재전송 유령 메시지 방어] 발송된 지 120초 이상 지난 메시지는 답장하지 않고 스킵
            if msg_timestamp > 0 and (now - msg_timestamp > MAX_MESSAGE_AGE_SECONDS):
                age = now - msg_timestamp
                print(f"⏳ [오래된 재전송 메시지 스킵] 경과 시간: {age}초 (기준: {MAX_MESSAGE_AGE_SECONDS}초) | text='{msg_info.get('text')}'")
                return Response(content="EVENT_RECEIVED", status_code=200)

            sender_phone = msg_info.get("sender_phone")
            sender_name = msg_info.get("sender_name")
            text = msg_info.get("text")

            if text and sender_phone:
                print(f"\n📩 [WhatsApp 실시간 수신] {sender_name}({sender_phone}): '{text}'")
                try:
                    ai_reply = run_agent(user_message=text, sender_name=sender_name)
                    print(f"🤖 [AI 답변]\n{ai_reply}")
                    res = send_whatsapp_message(sender_phone, ai_reply)
                    print(f"📨 [WhatsApp 발송 완료]: {res}")
                except Exception as agent_err:
                    print(f"❌ 에이전트 오류: {agent_err}")
                    send_whatsapp_message(sender_phone, f"죄송합니다, {sender_name}님. 요청을 처리하는 중 일시적인 오류가 발생했습니다.")

        return Response(content="EVENT_RECEIVED", status_code=200)

    return Response(content="Method Not Allowed", status_code=405)
