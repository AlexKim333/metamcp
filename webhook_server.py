import os
import sys
import uvicorn
from fastapi import FastAPI, Request, Query, HTTPException, Response, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

from whatsapp_client import send_whatsapp_message, parse_incoming_message, get_account_status
from agent import run_agent

app = FastAPI(title="KTK WMS WhatsApp Agent Webhook Server")

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ktk_wms_webhook_secret_2026")

def process_and_reply(sender_phone: str, sender_name: str, text: str):
    """
    백그라운드에서 AI 에이전트 실행 후 WhatsApp으로 답변 전송
    (Webhook 200 OK 응답 타임아웃 방지)
    """
    print(f"\n🧠 [AI 에이전트 처리 시작] from={sender_name}({sender_phone}) | query='{text}'")
    ai_reply = run_agent(user_message=text, sender_name=sender_name)
    print(f"🤖 [AI 답변 생성 완료]\n{ai_reply}")
    
    print(f"📤 [WhatsApp 회신 발송] to={sender_phone}...")
    res = send_whatsapp_message(sender_phone, ai_reply)
    print(f"📨 [WhatsApp 발송 결과]: {res}")

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
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    WhatsApp으로부터 실시간 메시지 수신 시 호출되는 엔드포인트
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
        
        if text:
            print(f"\n📩 [WhatsApp 메시지 도착] 발신자: {sender_name} ({sender_phone}) | 내용: '{text}'")
            # 백그라운드 태스크로 AI 에이전트 실행 및 회신 전송
            background_tasks.add_task(process_and_reply, sender_phone, sender_name, text)

    # Meta 서버에는 지체 없이 200 OK를 응답
    return Response(content="EVENT_RECEIVED", status_code=200)

if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8000, reload=True)
