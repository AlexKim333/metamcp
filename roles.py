import os
import re
from typing import Dict, Any, Optional, List
from config_manager import get_settings

ROLE_OWNER = "owner"
ROLE_STAFF = "staff"
ROLE_CUSTOMER = "customer"

def clean_phone_number(phone: str) -> str:
    return re.sub(r'[^0-9]', '', str(phone or ''))

def get_user_role(phone_number: str) -> Dict[str, Any]:
    clean_phone = clean_phone_number(phone_number)
    settings = get_settings()
    
    owner_phones = [clean_phone_number(p) for p in settings.get("owner_phones", [])]
    staff_members = settings.get("staff_members", [])

    # 1. 최고 관리자 (Owner)
    if clean_phone in owner_phones:
        return {
            "role": ROLE_OWNER,
            "role_name": "오너/최고관리자",
            "phone": clean_phone,
            "can_view_all_warehouses": True,
            "can_view_costs": True,
            "can_create_transfer": True
        }
        
    # 2. 지점/현장 직원 (Staff)
    for staff in staff_members:
        if clean_phone == clean_phone_number(staff.get("phone", "")):
            return {
                "role": ROLE_STAFF,
                "role_name": "직원",
                "phone": clean_phone,
                "name": staff.get("name", "직원"),
                "branch": staff.get("branch", "[MAIN] ALARCON"),
                "can_view_all_warehouses": True,
                "can_view_costs": False,
                "can_create_transfer": True
            }

    # 3. 일반 고객 / 외부 바이어 (Customer)
    return {
        "role": ROLE_CUSTOMER,
        "role_name": "일반고객",
        "phone": clean_phone,
        "can_view_all_warehouses": False,
        "can_view_costs": False,
        "can_create_transfer": False
    }

def get_staff_by_branch(branch_name: str) -> Optional[Dict[str, Any]]:
    """지점명으로 해당 지점의 전담 담당자 정보 조회"""
    settings = get_settings()
    for staff in settings.get("staff_members", []):
        if staff.get("branch", "").lower() in branch_name.lower() or branch_name.lower() in staff.get("branch", "").lower():
            return staff
    return None
