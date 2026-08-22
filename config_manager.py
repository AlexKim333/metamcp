import os
import json
from typing import Dict, Any, List

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "admin_password": os.getenv("ADMIN_PASSWORD", "ladypolo2026!"),
    "max_auto_order_limit": 50000,
    "strict_business_guardrail": True,
    "show_quick_buttons": True,
    "default_language": "es",
    "customer_channel": "whatsapp",
    "staff_channel": "telegram",
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "telegram_webhook_secret": "ladypolo_telegram_secret_2026",
    "tenant_custom_rules": [
        "1회 주문 금액이 임계 금액(50,000 MXN)을 초과하는 대량 주문은 담당 지점장 1:1 상담방(wa.me 딥링크)으로 자동 안내한다."
    ],
    "owner_phones": ["5215563482005"],
    "staff_members": [
        {"name": "Monse", "phone": "5215512345678", "branch": "IKEA", "role": "지점 매니저"},
        {"name": "Nadya", "phone": "5215587654321", "branch": "TIENDA", "role": "매장 매니저"}
    ],
    "branches": ["[MAIN] ALARCON", "IKEA", "PANTACO", "PINO", "TLANEPANTLA", "ARGENTINA", "ARGENTINA2", "AZTECAS", "CARMEN", "TIENDA"]
}

_runtime_settings: Dict[str, Any] = {}

def get_settings() -> Dict[str, Any]:
    global _runtime_settings
    if _runtime_settings:
        return _runtime_settings

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                _runtime_settings = {**DEFAULT_SETTINGS, **saved}
        except Exception as e:
            print(f"⚠️ settings.json 읽기 오류: {e}")

    if not _runtime_settings:
        _runtime_settings = DEFAULT_SETTINGS.copy()

    # Supabase 클라우드 실시간 데이터 동기화
    try:
        from supabase_client import (
            get_active_tenant_rules,
            get_supabase_staff_members,
            get_supabase_owner_phones,
            get_supabase_tenant_settings
        )
        s_rules = get_active_tenant_rules()
        if s_rules:
            _runtime_settings["tenant_custom_rules"] = s_rules

        s_staff = get_supabase_staff_members()
        if s_staff:
            _runtime_settings["staff_members"] = s_staff

        s_owners = get_supabase_owner_phones()
        if s_owners:
            _runtime_settings["owner_phones"] = s_owners

        s_settings = get_supabase_tenant_settings()
        if s_settings:
            _runtime_settings["max_auto_order_limit"] = s_settings.get("max_auto_order_limit", 50000)
            _runtime_settings["strict_business_guardrail"] = s_settings.get("strict_business_guardrail", True)
            _runtime_settings["show_quick_buttons"] = s_settings.get("show_quick_buttons", True)
            _runtime_settings["customer_channel"] = s_settings.get("customer_channel", "whatsapp")
            _runtime_settings["staff_channel"] = s_settings.get("staff_channel", "telegram")
            _runtime_settings["telegram_bot_token"] = s_settings.get("telegram_bot_token", "")
    except Exception as e:
        print(f"⚠️ Supabase 실시간 동기화 예외: {e}")

    return _runtime_settings

def save_settings(new_settings: Dict[str, Any]) -> bool:
    global _runtime_settings
    try:
        merged = {**get_settings(), **new_settings}
        _runtime_settings = merged
        
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # Supabase 클라우드 동기화
        try:
            from supabase_client import update_supabase_tenant_settings
            update_supabase_tenant_settings(merged)
        except Exception as e:
            print(f"⚠️ Supabase 설정 동기화 예외: {e}")
            
        return True
    except Exception as e:
        print(f"❌ 설정 저장 오류: {e}")
        return False

def add_tenant_custom_rule(rule_text: str, changed_by_phone: str = "admin", changed_by_name: str = "오너", channel: str = "whatsapp") -> bool:
    settings = get_settings()
    rules = settings.get("tenant_custom_rules", [])
    if rule_text not in rules:
        rules.append(rule_text)
        settings["tenant_custom_rules"] = rules
        save_settings(settings)

    try:
        from supabase_client import add_tenant_rule_to_supabase
        add_tenant_rule_to_supabase(
            rule_content=rule_text,
            changed_by_phone=changed_by_phone,
            changed_by_name=changed_by_name,
            channel=channel
        )
    except Exception as e:
        print(f"⚠️ Supabase 룰북 저장 예외: {e}")

    return True
