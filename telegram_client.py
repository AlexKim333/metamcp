import os
import requests
from typing import Optional, Dict, Any, List
from config_manager import get_settings

def get_bot_token() -> str:
    settings = get_settings()
    return settings.get("telegram_bot_token") or os.getenv("TELEGRAM_BOT_TOKEN", "")

def send_telegram_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> Dict[str, Any]:
    """텔레그램 텍스트 메시지 발송 (비용 0원 무제한)"""
    token = get_bot_token()
    if not token:
        print("⚠️ 텔레그램 봇 토큰이 설정되지 않았습니다 (대시보드에서 등록 필요).")
        return {"success": False, "error": "No telegram_bot_token"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        print(f"❌ 텔레그램 발송 오류: {e}")
        return {"success": False, "error": str(e)}

def send_telegram_keyboard(chat_id: str, text: str, buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    """텔레그램 인라인 키보드(버튼) 발송 (비용 0원)"""
    token = get_bot_token()
    if not token:
        return {"success": False, "error": "No telegram_bot_token"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": buttons
        }
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def set_telegram_webhook(webhook_url: str) -> Dict[str, Any]:
    """텔레그램 봇 Webhook URL 등록"""
    token = get_bot_token()
    if not token:
        return {"success": False, "error": "No telegram_bot_token"}

    url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload = {"url": webhook_url}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
