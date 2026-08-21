import os
import sys
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
API_VERSION = os.getenv("META_API_VERSION", "v19.0")
BASE_URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def send_text(to_number: str, message: str):
    print(f"\n📤 1. [{to_number}] 번호로 일반 텍스트(' {message} ') 발송 시도...")
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    res = requests.post(BASE_URL, headers=headers, json=payload, timeout=10)
    print(f"HTTP Status: {res.status_code}")
    print(f"Response: {res.json()}")
    return res.status_code == 200, res.json()

def send_template(to_number: str, template_name: str = "hello_world"):
    print(f"\n📤 2. [{to_number}] 번호로 기본 승인 템플릿('{template_name}') 발송 시도...")
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "en_US"
            }
        }
    }
    res = requests.post(BASE_URL, headers=headers, json=payload, timeout=10)
    print(f"HTTP Status: {res.status_code}")
    print(f"Response: {res.json()}")
    return res.status_code == 200, res.json()

if __name__ == "__main__":
    raw_number = "5563482005"
    if len(sys.argv) > 1:
        raw_number = sys.argv[1]
    
    # 멕시코 국가코드 접두사 처리 (52 / 521)
    targets = [
        f"521{raw_number}",   # 5215563482005 (WhatsApp 표준 모바일)
        f"52{raw_number}",    # 525563482005
    ]
    
    print("=" * 60)
    print(f"📱 WhatsApp 발송 테스트 대상: {raw_number}")
    print("=" * 60)

    for target in targets:
        print(f"\n👉 대상 번호 형식 시도: {target}")
        success, data = send_text(target, "안녕하세요! KTK WMS 에이전트 연동 테스트 메시지입니다.")
        if success:
            print("🎉 일반 텍스트 발송 성공!")
            break
        else:
            error_code = data.get("error", {}).get("code")
            print(f"ℹ️ 일반 텍스트 실패 (에러코드: {error_code}). 템플릿 발송 시도...")
            t_success, t_data = send_template(target, "hello_world")
            if t_success:
                print("🎉 템플릿 메시지 발송 성공!")
                break
