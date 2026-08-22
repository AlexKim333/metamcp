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

def get_active_tenant_rules(tenant_id: str = "ladypolo_mexico") -> List[str]:
    """Supabase에서 현재 활성화된 매장 룰북 목록 조회"""
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
            rows = res.json()
            return [r.get("rule_content") for r in rows if r.get("rule_content")]
        else:
            print(f"⚠️ Supabase 룰북 조회 실패 ({res.status_code}): {res.text}")
            return []
    except Exception as e:
        print(f"⚠️ Supabase 룰북 조회 예외: {e}")
        return []

def add_tenant_rule_to_supabase(
    rule_content: str,
    changed_by_phone: str = "admin",
    changed_by_name: str = "오너",
    channel: str = "whatsapp",
    tenant_id: str = "ladypolo_mexico"
) -> bool:
    """Supabase 룰북에 새 규칙 추가 및 변경 이력 감사 로그(Audit Log) 자동 기록"""
    headers = _get_headers()

    # 1. tenant_rules 테이블에 삽입
    rule_url = f"{SUPABASE_URL}/rest/v1/tenant_rules"
    rule_payload = {
        "tenant_id": tenant_id,
        "rule_content": rule_content.strip(),
        "created_by": changed_by_name or changed_by_phone,
        "is_active": True
    }

    try:
        res1 = requests.post(rule_url, headers=headers, json=rule_payload, timeout=5)
        if res1.status_code not in [200, 201]:
            print(f"❌ 룰북 저장 실패: {res1.text}")
            return False

        # 2. rulebook_audit_logs 테이블에 감사 로그 기록
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
    except Exception as e:
        print(f"❌ Supabase 룰북 추가 오류: {e}")
        return False

def get_rulebook_audit_logs(limit: int = 20, tenant_id: str = "ladypolo_mexico") -> List[Dict[str, Any]]:
    """대시보드 검토용: 최근 룰북 변경 이력(누가 언제 바꿨는지) 감사 로그 조회"""
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
    except Exception as e:
        print(f"❌ 감사 로그 조회 오류: {e}")
        return []
