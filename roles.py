import os
from typing import Dict, Any, Optional

ROLE_OWNER = "owner"
ROLE_STAFF = "staff"
ROLE_CUSTOMER = "customer"

def get_user_role(sender_phone: str) -> Dict[str, Any]:
    """전화번호로 사용자 역할(오너, 직원, 고객) 동적 식별 (Supabase Cloud 연동)"""
    if not sender_phone:
        return {"role": ROLE_CUSTOMER, "name": "고객님", "branch": None}

    clean_phone = sender_phone.replace("+", "").replace("-", "").replace(" ", "").strip()

    # 1. Supabase Cloud 실시간 조회 시도
    try:
        from supabase_client import get_supabase_owner_phones, get_supabase_staff_members
        owners = get_supabase_owner_phones()
        for op in owners:
            clean_op = op.replace("+", "").replace("-", "").replace(" ", "").strip()
            if clean_phone.endswith(clean_op) or clean_op.endswith(clean_phone):
                return {
                    "role": ROLE_OWNER,
                    "name": "대표님(Owner)",
                    "branch": "[MAIN] ALARCON"
                }

        staff_list = get_supabase_staff_members()
        for st in staff_list:
            st_phone = st.get("phone", "").replace("+", "").replace("-", "").replace(" ", "").strip()
            if clean_phone.endswith(st_phone) or st_phone.endswith(clean_phone):
                return {
                    "role": ROLE_STAFF,
                    "name": st.get("name", "직원"),
                    "branch": st.get("branch", "IKEA"),
                    "position": st.get("role", "지점 매니저")
                }
    except Exception as e:
        print(f"⚠️ Supabase 권한 조회 실패, 로컬 폴백: {e}")

    # 2. 로컬 설정 폴백
    from config_manager import get_settings
    settings = get_settings()

    for op in settings.get("owner_phones", []):
        clean_op = op.replace("+", "").replace("-", "").replace(" ", "").strip()
        if clean_phone.endswith(clean_op) or clean_op.endswith(clean_phone):
            return {
                "role": ROLE_OWNER,
                "name": "대표님(Owner)",
                "branch": "[MAIN] ALARCON"
            }

    for st in settings.get("staff_members", []):
        st_phone = st.get("phone", "").replace("+", "").replace("-", "").replace(" ", "").strip()
        if clean_phone.endswith(st_phone) or st_phone.endswith(clean_phone):
            return {
                "role": ROLE_STAFF,
                "name": st.get("name", "직원"),
                "branch": st.get("branch", "IKEA"),
                "position": st.get("role", "지점 매니저")
            }

    # 3. 미등록 외부 번호 ➔ 일반 고객
    return {
        "role": ROLE_CUSTOMER,
        "name": "고객님",
        "branch": None
    }

def get_branch_manager_phone(branch_name: str) -> Optional[str]:
    """지점 전담 매니저의 WhatsApp 전화번호 조회 (Supabase 연동)"""
    if not branch_name:
        return "5215512345678"

    clean_b = branch_name.lower().replace("[sub]", "").replace("[main]", "").replace("- k", "").strip()

    try:
        from supabase_client import get_supabase_staff_members
        staff_list = get_supabase_staff_members()
        for st in staff_list:
            st_b = st.get("branch", "").lower()
            if clean_b in st_b or st_b in clean_b:
                return st.get("phone")
    except Exception:
        pass

    from config_manager import get_settings
    settings = get_settings()
    for st in settings.get("staff_members", []):
        st_b = st.get("branch", "").lower()
        if clean_b in st_b or st_b in clean_b:
            return st.get("phone")

    return "5215512345678"
