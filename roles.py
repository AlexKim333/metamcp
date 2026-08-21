import os
import re
from typing import Dict, Any, Optional

ROLE_OWNER = "owner"
ROLE_STAFF = "staff"
ROLE_CUSTOMER = "customer"

# 관리자/대표님 전화번호 목록
OWNER_PHONES = {
    "5215563482005",
    "525563482005",
}

# 직원 전화번호 목록
STAFF_PHONES = {}

def clean_phone_number(phone: str) -> str:
    return re.sub(r'[^0-9]', '', str(phone or ''))

def get_user_role(phone_number: str) -> Dict[str, Any]:
    clean_phone = clean_phone_number(phone_number)
    
    # 1. 최고 관리자 (Owner)
    if clean_phone in OWNER_PHONES:
        return {
            "role": ROLE_OWNER,
            "role_name": "오너/최고관리자",
            "phone": clean_phone,
            "can_view_all_warehouses": True,
            "can_view_costs": True,
            "can_create_transfer": True
        }
        
    # 2. 지점/현장 직원 (Staff)
    if clean_phone in STAFF_PHONES:
        staff_info = STAFF_PHONES[clean_phone]
        return {
            "role": ROLE_STAFF,
            "role_name": "직원",
            "phone": clean_phone,
            "name": staff_info.get("name", "직원"),
            "can_view_all_warehouses": True,
            "can_view_costs": False,
            "can_create_transfer": True
        }

    # 3. 일반 고객 / 외부 바이어 (Customer)
    # 고객도 재고 수량(박스/개수)을 명확하게 확인할 수 있도록 허용
    return {
        "role": ROLE_CUSTOMER,
        "role_name": "일반고객",
        "phone": clean_phone,
        "can_view_all_warehouses": False,
        "can_view_costs": False,
        "can_create_transfer": False
    }
