import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import PlainTextResponse, JSONResponse, HTMLResponse
from dotenv import load_dotenv

load_dotenv()

from whatsapp_client import (
    send_whatsapp_message,
    send_interactive_buttons,
    parse_incoming_message,
    get_account_status
)
from agent import run_agent
from text_preprocessor import (
    try_zero_token_local_bypass,
    handle_quick_button_click,
    detect_and_update_user_lang
)
from config_manager import get_settings, save_settings
from dashboard_ui import get_dashboard_html

app = FastAPI(title="ladypolo WhatsApp Agent & Admin Portal on Vercel")

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ktk_wms_webhook_secret_2026")
MAX_MESSAGE_AGE_SECONDS = 120

@app.api_route("/{full_path:path}", methods=["GET", "POST"])
async def handle_all_requests(request: Request, full_path: str = ""):
    method = request.method
    query_params = request.query_params
    
    # URL 경로 다각도 검사 (full_path 또는 request.url.path 모두 대응)
    raw_path = request.url.path.strip("/").lower()
    fp_path = full_path.strip("/").lower()
    combined_path = f"{raw_path} {fp_path}"

    # =========================================================================
    # 1. API 엔드포인트 처리 (POST /api/login, GET/POST /api/settings, /api/test-agent)
    # =========================================================================
    if "api/login" in combined_path and method == "POST":
        try:
            data = await request.json()
            pwd = data.get("password")
            settings = get_settings()
            if pwd == settings.get("admin_password"):
                return JSONResponse({"success": True, "token": "authenticated"})
            return JSONResponse({"success": False, "error": "Invalid password"}, status_code=401)
        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)

    if "api/settings" in combined_path:
        if method == "GET":
            return JSONResponse(get_settings())
        elif method == "POST":
            try:
                new_data = await request.json()
                ok = save_settings(new_data)
                return JSONResponse({"success": ok, "settings": get_settings()})
            except Exception as e:
                return JSONResponse({"success": False, "error": str(e)}, status_code=400)

    if "api/test-agent" in combined_path and method == "POST":
        try:
            data = await request.json()
            msg = data.get("message", "").strip()
            if not msg:
                return JSONResponse({"reply": "메시지를 입력해 주세요."})
            
            lang = "es" if any(s in msg.lower() for s in ['hola', 'stock', 'cuanto', 'precio', 'uva']) else "ko"
            reply = run_agent(user_message=msg, sender_name="Admin", sender_phone="5215563482005", user_lang=lang)
            return JSONResponse({"reply": reply})
        except Exception as e:
            return JSONResponse({"reply": f"오류 발생: {e}"})

    # =========================================================================
    # 2. GET 요청 (Meta Webhook Verification 또는 관리자 대시보드 HTML)
    # =========================================================================
    if method == "GET":
        mode = query_params.get("hub.mode")
        token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        if mode == "subscribe":
            if token == VERIFY_TOKEN:
                return PlainTextResponse(content=str(challenge), status_code=200)
            else:
                raise HTTPException(status_code=403, detail="Verification token mismatch")

        # 브라우저 접속은 대시보드 HTML 서빙
        return HTMLResponse(content=get_dashboard_html(), status_code=200)

    # =========================================================================
    # 3. POST 요청: Meta WhatsApp Cloud API 실시간 웹훅 수신
    # =========================================================================
    elif method == "POST":
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(content={"status": "invalid json"}, status_code=400)

        msg_info = parse_incoming_message(body)
        
        if msg_info:
            msg_timestamp = msg_info.get("timestamp", 0)
            now = int(time.time())
            
            if msg_timestamp > 0 and (now - msg_timestamp > MAX_MESSAGE_AGE_SECONDS):
                print(f"⏳ [오래된 재전송 메시지 스킵] 경과 시간: {now - msg_timestamp}초 | text='{msg_info.get('text')}'")
                return Response(content="EVENT_RECEIVED", status_code=200)

            sender_phone = msg_info.get("sender_phone")
            sender_name = msg_info.get("sender_name")
            button_id = msg_info.get("button_id")
            text = msg_info.get("text", "")

            if sender_phone:
                user_lang = detect_and_update_user_lang(sender_phone, text)
                print(f"\n🌐 [세션 언어] {sender_name}({sender_phone}) ➔ {user_lang.upper()}")

                if button_id:
                    print(f"🔘 [버튼 클릭] button_id='{button_id}'")
                    reply_text = handle_quick_button_click(button_id, sender_name, user_lang=user_lang)
                    send_whatsapp_message(sender_phone, reply_text)
                    return Response(content="EVENT_RECEIVED", status_code=200)

                if text:
                    print(f"📩 [수신] {sender_name}: '{text}'")
                    bypass_res = try_zero_token_local_bypass(text, sender_name, user_lang=user_lang)
                    
                    if bypass_res:
                        if bypass_res.get("type") == "buttons":
                            p = bypass_res["payload"]
                            send_interactive_buttons(
                                recipient_phone=sender_phone,
                                body_text=p["body_text"],
                                buttons=p["buttons"],
                                footer_text="ladypolo AI Assistant"
                            )
                            return Response(content="EVENT_RECEIVED", status_code=200)
                        elif bypass_res.get("type") == "text":
                            send_whatsapp_message(sender_phone, bypass_res["content"])
                            return Response(content="EVENT_RECEIVED", status_code=200)

                    try:
                        ai_reply = run_agent(
                            user_message=text,
                            sender_name=sender_name,
                            sender_phone=sender_phone,
                            user_lang=user_lang
                        )
                        send_whatsapp_message(sender_phone, ai_reply)
                    except Exception as agent_err:
                        print(f"❌ 에이전트 오류: {agent_err}")
                        err_msg = (
                            f"Disculpa, {sender_name}. Ocurrió un error temporal al procesar tu solicitud."
                            if user_lang == "es" else
                            f"죄송합니다, {sender_name}님. 요청을 처리하는 중 일시적인 오류가 발생했습니다."
                        )
                        send_whatsapp_message(sender_phone, err_msg)

        return Response(content="EVENT_RECEIVED", status_code=200)

    return Response(content="Method Not Allowed", status_code=405)
