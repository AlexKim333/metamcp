import os
import sys
import uvicorn
from fastapi import FastAPI, Request, Query, HTTPException, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from whatsapp_client import send_whatsapp_message, parse_incoming_message, get_account_status

load_dotenv()

app = FastAPI(title="KTK WMS WhatsApp Agent Webhook Server")

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ktk_wms_webhook_secret_2026")

@app.get("/")
def root():
    return {"status": "ok", "service": "KTK WMS WhatsApp Webhook Server"}

@app.get("/health")
def health_check():
    account_info = get_account_status()
    return {
        "status": "healthy",
        "whatsapp_account": account_info
    }

@app.get("/webhook")
def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """
    Meta 개발자 포털에서 Webhook URL 등록 시 호출되는 검증 엔드포인트
    """
    print(f"🔔 [Webhook Verification Request] mode={mode}, token={token}")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook Verification 성공! (Challenge 반환)")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            print("❌ Webhook Verification 실패: Verify Token 불일치")
            raise HTTPException(status_code=403, detail="Verification token mismatch")
            
    raise HTTPException(status_code=400, detail="Missing parameters")

@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    WhatsApp으로부터 메시지 수신 시 호출되는 엔드포인트
    """
    try:
        body = await request.json()
    except Exception as e:
        print(f"❌ JSON 파싱 실패: {e}")
        return JSONResponse(content={"status": "invalid json"}, status_code=400)

    # 1. 메시지 파싱
    msg_info = parse_incoming_message(body)
    
    if msg_info:
        sender_phone = msg_info["sender_phone"]
        sender_name = msg_info["sender_name"]
        text = msg_info["text"]
        
        print(f"\n📩 [WhatsApp 수신] 발신자: {sender_name} ({sender_phone}) | 내용: '{text}'")
        
        # 1단계 에코 응답 (테스트용)
        reply_text = f"🤖 [KTK WMS 에이전트]\n안녕하세요, {sender_name}님!\n보내주신 메시지를 정상적으로 수신했습니다:\n\"{text}\"\n\n(현재 1단계 연동 테스트 진행 중입니다.)"
        
        print(f"📤 [WhatsApp 회신 발송 중] to={sender_phone}...")
        res = send_whatsapp_message(sender_phone, reply_text)
        print(f"📨 [WhatsApp 발송 결과] {res}")

    # Meta 서버에는 항상 200 OK를 빠르게 응답해야 재전송 루프가 발생하지 않음
    return Response(content="EVENT_RECEIVED", status_code=200)

if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8000, reload=True)
