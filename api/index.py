import os
import sys

# 프로젝트 루트 디렉토리를 Python Path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, Request, Query, HTTPException, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

from whatsapp_client import send_whatsapp_message, parse_incoming_message, get_account_status
from agent import run_agent

app = FastAPI(title="KTK WMS WhatsApp Agent on Vercel")

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ktk_wms_webhook_secret_2026")

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "KTK WMS WhatsApp AI Agent",
        "platform": "Vercel Serverless"
    }

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
    Meta 개발자 포털 Webhook Verification 핸들러
    """
    print(f"🔔 [Webhook Verification] mode={mode}, token={token}")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook Verification 성공! (Challenge 반환)")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            print("❌ Webhook Verification 실패: Token 불일치")
            raise HTTPException(status_code=403, detail="Verification token mismatch")
            
    raise HTTPException(status_code=400, detail="Missing parameters")

@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    WhatsApp 실시간 메시지 수신 및 AI 자동 응답 핸들러
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
            print(f"\n📩 [WhatsApp 수신] {sender_name}({sender_phone}): '{text}'")
            try:
                # 2. AI 에이전트 실행 및 답변 생성
                ai_reply = run_agent(user_message=text, sender_name=sender_name)
                print(f"🤖 [AI 답변]\n{ai_reply}")
                
                # 3. WhatsApp 메시지 발송
                res = send_whatsapp_message(sender_phone, ai_reply)
                print(f"📨 [발송 완료]: {res}")
            except Exception as agent_err:
                print(f"❌ 메시지 처리 중 오류: {agent_err}")
                # 오류 발생 시 기본 안내 메시지 발송 시도
                send_whatsapp_message(sender_phone, f"죄송합니다, {sender_name}님. 요청을 처리하는 중 일시적인 오류가 발생했습니다.")

    # Meta 서버에 200 OK 응답 반환
    return Response(content="EVENT_RECEIVED", status_code=200)

# 로컬 단독 실행 지원
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)
