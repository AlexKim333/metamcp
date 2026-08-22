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
from telegram_client import (
    send_telegram_message,
    send_telegram_keyboard,
    set_telegram_webhook
)
from agent import run_agent
from text_preprocessor import (
    try_zero_token_local_bypass,
    handle_quick_button_click,
    detect_and_update_user_lang
)
from config_manager import get_settings, save_settings
from dashboard_ui import get_dashboard_html

app = FastAPI(title="ladypolo WhatsApp & Telegram Agent Portal on Vercel")

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ktk_wms_webhook_secret_2026")
MAX_MESSAGE_AGE_SECONDS = 120

@app.api_route("/{full_path:path}", methods=["GET", "POST"])
async def handle_all_requests(request: Request, full_path: str = ""):
    method = request.method
    query_params = request.query_params
    path = full_path.strip("/").lower()

    # =========================================================================
    # 1. GET 요청 (Meta Webhook Verification 또는 관리자 대시보드 HTML)
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

        # 브라우저 접속은 관리자 대시보드 HTML 서빙
        return HTMLResponse(content=get_dashboard_html(), status_code=200)

    # =========================================================================
    # 2. POST 요청: Action API / Telegram Webhook / Meta WhatsApp Webhook
    # =========================================================================
    elif method == "POST":
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(content={"status": "invalid json"}, status_code=400)

        # ---------------------------------------------------------------------
        # [A. 관리자 대시보드 Action 처리]
        # ---------------------------------------------------------------------
        action = body.get("action")
        if action:
            if action == "login":
                pwd = body.get("password")
                settings = get_settings()
                if pwd == settings.get("admin_password"):
                    return JSONResponse({"success": True, "token": "authenticated"})
                return JSONResponse({"success": False, "error": "Invalid password"}, status_code=401)

            elif action == "get_settings":
                return JSONResponse(get_settings())

            elif action == "get_audit_logs":
                try:
                    from supabase_client import get_rulebook_audit_logs
                    logs = get_rulebook_audit_logs(limit=30)
                    return JSONResponse({"logs": logs})
                except Exception as e:
                    return JSONResponse({"logs": [], "error": str(e)})

            elif action == "save_settings":
                new_settings = body.get("settings", {})
                ok = save_settings(new_settings)
                return JSONResponse({"success": ok, "settings": get_settings()})

            elif action == "register_telegram_webhook":
                token = body.get("token")
                if token:
                    save_settings({"telegram_bot_token": token})
                webhook_url = f"https://{request.url.netloc}/webhook/telegram"
                res = set_telegram_webhook(webhook_url)
                return JSONResponse({"success": res.get("ok", False), "result": res})

            elif action == "test_agent":
                msg = body.get("message", "").strip()
                if not msg:
                    return JSONResponse({"reply": "메시지를 입력해 주세요."})
                lang = "es" if any(s in msg.lower() for s in ['hola', 'stock', 'cuanto', 'precio', 'uva']) else "ko"
                reply = run_agent(user_message=msg, sender_name="Admin", sender_phone="5215563482005", user_lang=lang)
                return JSONResponse({"reply": reply})

        # ---------------------------------------------------------------------
        # [B. Telegram 봇 인바운드 웹훅 수신 (사내 직원 전용 - 비용 0원)]
        # ---------------------------------------------------------------------
        if "update_id" in body and ("message" in body or "callback_query" in body):
            try:
                tg_msg = body.get("message", {})
                chat_id = str(tg_msg.get("chat", {}).get("id", ""))
                sender_name = tg_msg.get("from", {}).get("first_name", "Staff")
                text = tg_msg.get("text", "").strip()

                if chat_id and text:
                    print(f"✈️ [Telegram 수신] {sender_name}({chat_id}): '{text}'")
                    # 언어 감지 및 에이전트 실행
                    user_lang = "es" if any(s in text.lower() for s in ['hola', 'stock', 'cuanto', 'cajas']) else "ko"
                    
                    if text in ["/start", "안녕", "hola", "메뉴"]:
                        # 텔레그램 시작 인사 및 키보드
                        welcome_text = (
                            f"👋 안녕하세요, {sender_name}님! **ladypolo 사내 AI 비서 (무료 텔레그램)**입니다.\n\n"
                            f"📦 **재고 조회:** `P160 검정` 또는 `021G 파랑`을 바로 입력하세요.\n"
                            f"🚚 **재고 이동:** 품목들을 조회한 후 `이것들 1박스씩 이동 전표 넣어줘`라고 톡하세요!"
                        )
                        buttons = [
                            [{"text": "📦 P160 재고 조회", "callback_data": "stock_p160"}, {"text": "📋 최근 전표", "callback_data": "recent_transfers"}]
                        ]
                        send_telegram_keyboard(chat_id, welcome_text, buttons)
                    else:
                        ai_reply = run_agent(
                            user_message=text,
                            sender_name=sender_name,
                            sender_phone="5215512345678", # 사내 직원 권한 적용
                            user_lang=user_lang
                        )
                        send_telegram_message(chat_id, ai_reply)

                return JSONResponse({"ok": True})
            except Exception as tg_err:
                print(f"❌ 텔레그램 웹훅 오류: {tg_err}")
                return JSONResponse({"ok": False, "error": str(tg_err)})

        # ---------------------------------------------------------------------
        # [C. Meta WhatsApp Cloud API 실시간 웹훅 수신 (외부 고객 및 관리자)]
        # ---------------------------------------------------------------------
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
                    print(f"📩 [WhatsApp 수신] {sender_name}: '{text}'")
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
