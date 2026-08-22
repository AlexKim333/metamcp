import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dxsvkwmemzxgqancqqqc.supabase.co").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_-zriQgPBSW4VWr07BIBsbw_rTN5xUr4")

def _get_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

# =========================================================================
# 1. 룰북 & 감사 로그 (Tenant Rules & Audit Logs)
# =========================================================================
def get_active_tenant_rules(tenant_id: str = "ladypolo_mexico") -> List[str]:
    url = f"{SUPABASE_URL}/rest/v1/tenant_rules"
    headers = _get_headers()
    params = {
        "tenant_id": f"eq.{tenant_id}",
        "is_active": "eq.true",
        "order": "created_at.asc"
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            return [r.get("rule_content") for r in res.json() if r.get("rule_content")]
        return []
    except Exception:
        return []

def add_tenant_rule_to_supabase(
    rule_content: str,
    changed_by_phone: str = "admin",
    changed_by_name: str = "오너",
    channel: str = "whatsapp",
    tenant_id: str = "ladypolo_mexico"
) -> bool:
    headers = _get_headers()
    rule_url = f"{SUPABASE_URL}/rest/v1/tenant_rules"
    rule_payload = {
        "tenant_id": tenant_id,
        "rule_content": rule_content.strip(),
        "created_by": changed_by_name or changed_by_phone,
        "is_active": True
    }
    try:
        res1 = requests.post(rule_url, headers=headers, json=rule_payload, timeout=5)
        if res1.status_code in [200, 201]:
            audit_url = f"{SUPABASE_URL}/rest/v1/rulebook_audit_logs"
            audit_payload = {
                "tenant_id": tenant_id,
                "action": "ADD_RULE",
                "rule_content": rule_content.strip(),
                "changed_by_phone": changed_by_phone,
                "changed_by_name": changed_by_name,
                "channel": channel,
                "notes": "메신저/대시보드를 통한 실시간 룰 등록"
            }
            requests.post(audit_url, headers=headers, json=audit_payload, timeout=5)
            return True
        return False
    except Exception:
        return False

def get_rulebook_audit_logs(limit: int = 20, tenant_id: str = "ladypolo_mexico") -> List[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/rulebook_audit_logs"
    headers = _get_headers()
    params = {
        "tenant_id": f"eq.{tenant_id}",
        "order": "created_at.desc",
        "limit": str(limit)
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

# =========================================================================
# 2. 직원 및 RBAC 목록 (Staff Members)
# =========================================================================
def get_supabase_staff_members(tenant_id: str = "ladypolo_mexico") -> List[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/staff_members"
    headers = _get_headers()
    params = {
        "tenant_id": f"eq.{tenant_id}",
        "is_active": "eq.true",
        "order": "created_at.asc"
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

def add_supabase_staff_member(name: str, phone: str, branch: str, role: str = "지점 매니저", tenant_id: str = "ladypolo_mexico") -> bool:
    url = f"{SUPABASE_URL}/rest/v1/staff_members"
    headers = _get_headers()
    payload = {
        "tenant_id": tenant_id,
        "name": name.strip(),
        "phone": phone.strip(),
        "branch": branch.strip(),
        "role": role.strip(),
        "is_active": True
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        return res.status_code in [200, 201]
    except Exception:
        return False

def remove_supabase_staff_member(phone: str, tenant_id: str = "ladypolo_mexico") -> bool:
    url = f"{SUPABASE_URL}/rest/v1/staff_members"
    headers = _get_headers()
    params = {
        "tenant_id": f"eq.{tenant_id}",
        "phone": f"eq.{phone.strip()}"
    }
    try:
        res = requests.delete(url, headers=headers, params=params, timeout=5)
        return res.status_code in [200, 204]
    except Exception:
        return False

# =========================================================================
# 3. 오너 전화번호 목록 (Owner Phones)
# =========================================================================
def get_supabase_owner_phones(tenant_id: str = "ladypolo_mexico") -> List[str]:
    url = f"{SUPABASE_URL}/rest/v1/owner_phones"
    headers = _get_headers()
    params = {"tenant_id": f"eq.{tenant_id}"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            return [r.get("phone") for r in res.json() if r.get("phone")]
        return []
    except Exception:
        return []

# =========================================================================
# 4. 매장 통합 설정 (Tenant Settings)
# =========================================================================
def get_supabase_tenant_settings(tenant_id: str = "ladypolo_mexico") -> Optional[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/tenant_settings"
    headers = _get_headers()
    params = {"tenant_id": f"eq.{tenant_id}"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            rows = res.json()
            return rows[0] if rows else None
        return None
    except Exception:
        return None

def update_supabase_tenant_settings(new_settings: Dict[str, Any], tenant_id: str = "ladypolo_mexico") -> bool:
    url = f"{SUPABASE_URL}/rest/v1/tenant_settings"
    headers = _get_headers()
    params = {"tenant_id": f"eq.{tenant_id}"}
    payload = {
        "max_auto_order_limit": new_settings.get("max_auto_order_limit", 50000),
        "strict_business_guardrail": new_settings.get("strict_business_guardrail", True),
        "show_quick_buttons": new_settings.get("show_quick_buttons", True),
        "customer_channel": new_settings.get("customer_channel", "whatsapp"),
        "staff_channel": new_settings.get("staff_channel", "telegram"),
        "telegram_bot_token": new_settings.get("telegram_bot_token", ""),
        "updated_at": "now()"
    }
    try:
        res = requests.patch(url, headers=headers, params=params, json=payload, timeout=5)
        return res.status_code in [200, 204]
    except Exception:
        return False
