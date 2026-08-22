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
    
    # 📡 채널 매트릭스 설정 (외부 고객 vs 사내 직원)
    "customer_channel": "whatsapp",  # "whatsapp", "telegram", "both"
    "staff_channel": "telegram",      # "telegram", "whatsapp", "both"
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "telegram_webhook_secret": "ladypolo_telegram_secret_2026",
    
    # 📜 메신저 대화로 학습된 테넌트 커스텀 룰북
    "tenant_custom_rules": [
        "1회 주문 금액이 임계 금액(50,000 MXN)을 초과하는 대량 주문은 담당 지점장 1:1 상담방(wa.me 딥링크)으로 자동 안내한다.",
        "직원이 품목을 조회할 때는 본사 메인 창고([MAIN] ALARCON)와 해당 직원의 소속 지점 창고 재고를 최우선으로 안내한다."
    ],
    
    "owner_phones": [
        "5215563482005",
        "525563482005"
    ],
    "staff_members": [
        {
            "name": "Monse",
            "phone": "5215512345678",
            "branch": "IKEA",
            "role": "지점 매니저"
        },
        {
            "name": "Nadya",
            "phone": "5215587654321",
            "branch": "TIENDA",
            "role": "매장 매니저"
        }
    ],
    "branches": [
        "[MAIN] ALARCON",
        "IKEA",
        "PANTACO",
        "PINO",
        "TLANEPANTLA",
        "ARGENTINA",
        "ARGENTINA2",
        "AZTECAS",
        "CARMEN",
        "TIENDA"
    ]
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
                merged = {**DEFAULT_SETTINGS, **saved}
                _runtime_settings = merged
        except Exception as e:
            print(f"⚠️ settings.json 읽기 오류: {e}")

    if not _runtime_settings:
        _runtime_settings = DEFAULT_SETTINGS.copy()

    # Supabase 실시간 룰북 동기화 시도
    try:
        from supabase_client import get_active_tenant_rules
        supabase_rules = get_active_tenant_rules()
        if supabase_rules:
            _runtime_settings["tenant_custom_rules"] = supabase_rules
    except Exception:
        pass

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
            
        return True
    except Exception as e:
        print(f"❌ 설정 저장 오류: {e}")
        return False

def add_tenant_custom_rule(rule_text: str, changed_by_phone: str = "admin", changed_by_name: str = "오너", channel: str = "whatsapp") -> bool:
    """메신저 대화를 통해 실시간으로 Supabase 및 로컬 룰북에 새 규칙 추가"""
    settings = get_settings()
    rules = settings.get("tenant_custom_rules", [])
    if rule_text not in rules:
        rules.append(rule_text)
        settings["tenant_custom_rules"] = rules
        save_settings(settings)

    # Supabase 클라우드 DB에 영구 보관 및 감사 로그 기록
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
