import os
import json
from typing import Dict, Any, List

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "admin_password": os.getenv("ADMIN_PASSWORD", "ladypolo2026!"),
    "max_auto_order_limit": 50000,  # 5만 페소 이상 시 담당자 1:1 상담방으로 토스
    "strict_business_guardrail": True,  # 비업무 잡담 엄격 거절
    "show_quick_buttons": True,  # 3대 퀵 버튼 활성화
    "default_language": "es",  # 멕시코 기본 언어
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

# 런타임 메모리 캐시
_runtime_settings: Dict[str, Any] = {}

def get_settings() -> Dict[str, Any]:
    global _runtime_settings
    if _runtime_settings:
        return _runtime_settings

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                # 누락된 키 기본값 병합
                merged = {**DEFAULT_SETTINGS, **saved}
                _runtime_settings = merged
                return _runtime_settings
        except Exception as e:
            print(f"⚠️ settings.json 읽기 오류: {e}")

    _runtime_settings = DEFAULT_SETTINGS.copy()
    return _runtime_settings

def save_settings(new_settings: Dict[str, Any]) -> bool:
    global _runtime_settings
    try:
        merged = {**get_settings(), **new_settings}
        _runtime_settings = merged
        
        # 파일 쓰기 (로컬 및 영속성 지원 환경)
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Vercel Read-Only 환경에서는 메모리 캐시로 정상 지속
            
        return True
    except Exception as e:
        print(f"❌ 설정 저장 오류: {e}")
        return False
