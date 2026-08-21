import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
API_VERSION = os.getenv("META_API_VERSION", "v19.0")
BASE_URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}"

def get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

def get_account_status() -> Dict[str, Any]:
    """Meta WhatsApp 발신 전화번호 상태 조회"""
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}"
    try:
        res = requests.get(url, headers=get_headers(), timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def send_whatsapp_message(recipient_phone: str, text: str) -> Dict[str, Any]:
    """
    WhatsApp 일반 텍스트 메시지 발송
    :param recipient_phone: 수신자 전화번호 (국가번호 포함, '+' 제외, 예: 5216611234567 또는 821012345678)
    :param text: 발송할 메시지 본문
    """
    clean_phone = recipient_phone.replace("+", "").replace("-", "").replace(" ", "")
    url = f"{BASE_URL}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=10)
        return {
            "status_code": response.status_code,
            "data": response.json()
        }
    except Exception as e:
        return {
            "status_code": 500,
            "error": str(e)
        }

def send_whatsapp_template(recipient_phone: str, template_name: str = "hello_world", lang_code: str = "en_US") -> Dict[str, Any]:
    """
    WhatsApp 사전 승인된 템플릿 메시지 발송
    """
    clean_phone = recipient_phone.replace("+", "").replace("-", "").replace(" ", "")
    url = f"{BASE_URL}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": lang_code
            }
        }
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=10)
        return {
            "status_code": response.status_code,
            "data": response.json()
        }
    except Exception as e:
        return {
            "status_code": 500,
            "error": str(e)
        }

def parse_incoming_message(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Meta Webhook 페이로드로부터 사용자 메시지 정보 추출
    """
    try:
        entries = payload.get("entry", [])
        if not entries:
            return None
        
        changes = entries[0].get("changes", [])
        if not changes:
            return None
            
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None
            
        msg = messages[0]
        sender_phone = msg.get("from")
        msg_type = msg.get("type")
        msg_id = msg.get("id")
        msg_timestamp = int(msg.get("timestamp", 0))
        
        # 발신자 프로필 이름
        contacts = value.get("contacts", [])
        profile_name = contacts[0].get("profile", {}).get("name", "User") if contacts else "User"
        
        text_body = ""
        if msg_type == "text":
            text_body = msg.get("text", {}).get("body", "").strip()
        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            text_body = interactive.get("button_reply", {}).get("title") or interactive.get("list_reply", {}).get("title", "")
            
        return {
            "sender_phone": sender_phone,
            "sender_name": profile_name,
            "message_id": msg_id,
            "timestamp": msg_timestamp,
            "message_type": msg_type,
            "text": text_body,
            "raw": msg
        }
    except Exception as e:
        print(f"⚠️ Webhook 페이로드 파싱 중 오류: {e}")
        return None
