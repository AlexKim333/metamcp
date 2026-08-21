import os
import requests
from typing import Optional, Dict, Any, List
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

def send_interactive_buttons(
    recipient_phone: str,
    body_text: str,
    buttons: List[Dict[str, str]],
    header_text: str = "",
    footer_text: str = "ladypolo AI Assistant"
) -> Dict[str, Any]:
    """
    WhatsApp 인터랙티브 퀵 버튼 메시지 발송 (최대 3개 버튼)
    :param buttons: [{"id": "BTN_STOCK", "title": "📦 재고 조회"}, ...] (title 최대 20자)
    """
    clean_phone = recipient_phone.replace("+", "").replace("-", "").replace(" ", "")
    url = f"{BASE_URL}/messages"

    formatted_buttons = []
    for btn in buttons[:3]:
        formatted_buttons.append({
            "type": "reply",
            "reply": {
                "id": btn["id"],
                "title": btn["title"][:20]  # WhatsApp 제한 20자
            }
        })

    interactive_payload: Dict[str, Any] = {
        "type": "button",
        "body": {"text": body_text},
        "action": {"buttons": formatted_buttons}
    }

    if header_text:
        interactive_payload["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive_payload["footer"] = {"text": footer_text}

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "interactive",
        "interactive": interactive_payload
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
    Meta Webhook 페이로드로부터 사용자 메시지 정보 추출 (텍스트 & 버튼 클릭 지원)
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
        button_id = None

        if msg_type == "text":
            text_body = msg.get("text", {}).get("body", "").strip()
        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            itype = interactive.get("type")
            if itype == "button_reply":
                button_reply = interactive.get("button_reply", {})
                button_id = button_reply.get("id")
                text_body = button_reply.get("title", "").strip()
            elif itype == "list_reply":
                list_reply = interactive.get("list_reply", {})
                button_id = list_reply.get("id")
                text_body = list_reply.get("title", "").strip()
            
        return {
            "sender_phone": sender_phone,
            "sender_name": profile_name,
            "message_id": msg_id,
            "timestamp": msg_timestamp,
            "message_type": msg_type,
            "button_id": button_id,
            "text": text_body,
            "raw": msg
        }
    except Exception as e:
        print(f"⚠️ Webhook 페이로드 파싱 중 오류: {e}")
        return None
