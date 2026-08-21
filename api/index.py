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

from whatsapp_client import (
    send_whatsapp_message,
    send_interactive_buttons,
    parse_incoming_message,
    get_account_status
)
from agent import run_agent
from text_preprocessor import try_zero_token_local_bypass, handle_quick_button_click

app = FastAPI(title="ladypolo WhatsApp Agent on Vercel")

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ktk_wms_webhook_secret_2026")

# 최근 120초 내 유효 메시지만 처리 (과거 재전송 패킷 차단)
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
            
            # 과거 재전송 메시지 스킵
            if msg_timestamp > 0 and (now - msg_timestamp > MAX_MESSAGE_AGE_SECONDS):
                age = now - msg_timestamp
                print(f"⏳ [오래된 재전송 메시지 스킵] 경과 시간: {age}초 | text='{msg_info.get('text')}'")
                return Response(content="EVENT_RECEIVED", status_code=200)

            sender_phone = msg_info.get("sender_phone")
            sender_name = msg_info.get("sender_name")
            button_id = msg_info.get("button_id")
            text = msg_info.get("text")

            if sender_phone:
                # ---------------------------------------------------------
                # Case A: 사용자가 WhatsApp 인터랙티브 버튼을 탭한 경우 (0-Token)
                # ---------------------------------------------------------
                if button_id:
                    print(f"\n🔘 [버튼 클릭 감지] {sender_name}({sender_phone}): button_id='{button_id}'")
                    reply_text = handle_quick_button_click(button_id, sender_name)
                    res = send_whatsapp_message(sender_phone, reply_text)
                    print(f"📨 [버튼 응답 발송]: {res}")
                    return Response(content="EVENT_RECEIVED", status_code=200)

                # ---------------------------------------------------------
                # Case B: 일반 텍스트 입력
                # ---------------------------------------------------------
                if text:
                    print(f"\n📩 [WhatsApp 수신] {sender_name}({sender_phone}): '{text}'")

                    # 1. 0-Token 로컬 바이패스 검사
                    bypass_res = try_zero_token_local_bypass(text, sender_name)
                    
                    if bypass_res:
                        if bypass_res.get("type") == "buttons":
                            # 3대 퀵 버튼 발송
                            p = bypass_res["payload"]
                            print(f"🔘 [3대 퀵 버튼 발송] to={sender_phone}")
                            res = send_interactive_buttons(
                                recipient_phone=sender_phone,
                                body_text=p["body_text"],
                                buttons=p["buttons"],
                                footer_text="ladypolo AI Assistant"
                            )
                            print(f"📨 [버튼 발송 결과]: {res}")
                            return Response(content="EVENT_RECEIVED", status_code=200)
                        elif bypass_res.get("type") == "text":
                            # 로컬 텍스트 즉답 발송
                            print(f"⚡ [0-Token 로컬 즉답] to={sender_phone}")
                            res = send_whatsapp_message(sender_phone, bypass_res["content"])
                            print(f"📨 [로컬 발송 결과]: {res}")
                            return Response(content="EVENT_RECEIVED", status_code=200)

                    # 2. 복합 자연어 질문 -> Gemini 에이전트 실행 (역할 기반)
                    try:
                        ai_reply = run_agent(user_message=text, sender_name=sender_name, sender_phone=sender_phone)
                        print(f"🤖 [AI 답변]\n{ai_reply}")
                        res = send_whatsapp_message(sender_phone, ai_reply)
                        print(f"📨 [WhatsApp 발송 완료]: {res}")
                    except Exception as agent_err:
                        print(f"❌ 에이전트 오류: {agent_err}")
                        send_whatsapp_message(sender_phone, f"죄송합니다, {sender_name}님. 요청을 처리하는 중 일시적인 오류가 발생했습니다.")

        return Response(content="EVENT_RECEIVED", status_code=200)

    return Response(content="Method Not Allowed", status_code=405)
