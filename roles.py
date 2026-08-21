import os
import re
from typing import Dict, Any, Optional

# [기본 역할 정의]
# 1. OWNER: 모든 권한 (전 창고 상세 수량, 원가/도매단가, 전표 생성, 전체 시스템 제어)
# 2. STAFF: 직원 권한 (본사/지점 재고 확인, 지점 이동 전표 생성, 판매 단가)
# 3. CUSTOMER: 일반 고객 권한 (구매 가능 여부 확인, 고객 판매 단가, 상품 안내 / 내부 창고명 비공개)

ROLE_OWNER = "owner"
ROLE_STAFF = "staff"
ROLE_CUSTOMER = "customer"

# 관리자/대표님 전화번호 목록 (국제번호 기준, '+' 제외)
OWNER_PHONES = {
    "5215563482005",
    "525563482005",
}

# 기본 등록 직원 전화번호 목록
STAFF_PHONES = {
    # 예: "5215512345678": {"name": "Monse", "branch": "IKEA"},
}

def clean_phone_number(phone: str) -> str:
    """전화번호에서 공백, 하이픈, '+' 제거"""
    return re.sub(r'[^0-9]', '', str(phone or ''))

def get_user_role(phone_number: str) -> Dict[str, Any]:
    """
    발신자 전화번호를 기반으로 사용자 역할(Role)과 권한 메타데이터를 반환합니다.
    """
    clean_phone = clean_phone_number(phone_number)
    
    # 1. 최고 관리자 (Owner)
    if clean_phone in OWNER_PHONES:
        return {
            "role": ROLE_OWNER,
            "role_name": "오너/최고관리자",
            "phone": clean_phone,
            "can_view_all_warehouses": True,
            "can_view_costs": True,
            "can_create_transfer": True,
            "allowed_branches": "ALL"
        }
        
    # 2. 지점/현장 직원 (Staff)
    if clean_phone in STAFF_PHONES:
        staff_info = STAFF_PHONES[clean_phone]
        return {
            "role": ROLE_STAFF,
            "role_name": "직원",
            "phone": clean_phone,
            "name": staff_info.get("name", "직원"),
            "branch": staff_info.get("branch", "[MAIN] ALARCON"),
            "can_view_all_warehouses": True,
            "can_view_costs": False,
            "can_create_transfer": True,
            "allowed_branches": ["ALARCON", staff_info.get("branch")]
        }

    # 3. 일반 고객 / 외부인 (Customer - 기본값)
    return {
        "role": ROLE_CUSTOMER,
        "role_name": "일반고객",
        "phone": clean_phone,
        "can_view_all_warehouses": False,
        "can_view_costs": False,
        "can_create_transfer": False,
        "allowed_branches": []
    }
