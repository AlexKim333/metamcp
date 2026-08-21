import os
import sys
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# .env 파일 로드
load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
API_VERSION = os.getenv("META_API_VERSION", "v19.0")

def check_env():
    if not ACCESS_TOKEN or ACCESS_TOKEN == "your_permanent_system_user_token_here":
        print("❌ [.env] META_ACCESS_TOKEN이 설정되지 않았습니다.")
        return False
    if not PHONE_NUMBER_ID or PHONE_NUMBER_ID == "your_phone_number_id_here":
        print("❌ [.env] WHATSAPP_PHONE_NUMBER_ID가 설정되지 않았습니다.")
        return False
    return True

def get_phone_number_details():
    """발신 전화번호 ID 및 계정 상태 조회 (연결 테스트)"""
    print("\n🔍 1. WhatsApp 전화번호 계정 정보 확인 중...")
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if response.status_code == 200:
            print("✅ WhatsApp API 연결 성공!")
            print(f" - 표시 번호: {data.get('display_phone_number', 'N/A')}")
            print(f" - 인증 상태: {data.get('verified_name', 'N/A')}")
            print(f" - 계정 ID: {data.get('id', 'N/A')}")
            print(f" - 처리 상태: {data.get('code_verification_status', 'N/A')}")
            return True
        else:
            print(f"❌ 연결 실패 (HTTP {response.status_code}):")
            print(data)
            return False
    except Exception as e:
        print(f"❌ 네트워크 요청 실패: {e}")
        return False

def send_hello_world_template(recipient_phone: str):
    """
    기본 제공되는 hello_world 템플릿 메시지 발송 테스트
    :param recipient_phone: 국가번호 포함 수신번호 (예: 5216611309490 또는 821012345678, '+' 기호 제외)
    """
    clean_phone = recipient_phone.replace("+", "").replace("-", "").replace(" ", "")
    print(f"\n📤 2. '{clean_phone}' 번호로 테스트 템플릿(hello_world) 발송 중...")
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200:
            print("🎉 메시지 발송 성공!")
            print(f" - 메시지 ID: {data.get('messages', [{}])[0].get('id')}")
            return True
        else:
            print(f"❌ 발송 실패 (HTTP {response.status_code}):")
            print(data)
            return False
    except Exception as e:
        print(f"❌ 메시지 요청 오류: {e}")
        return False

if __name__ == "__main__":
    if check_env():
        if get_phone_number_details():
            if len(sys.argv) > 1:
                target_phone = sys.argv[1].strip()
                send_hello_world_template(target_phone)
            else:
                print("\n💡 실제 번호로 템플릿 발송 테스트를 원하시면 다음과 같이 실행하세요:")
                print("   python test_whatsapp.py <수신전화번호(국가번호포함)>")
