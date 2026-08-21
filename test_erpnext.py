import os
import sys
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

ERPNEXT_URL = os.getenv("ERPNEXT_URL", "https://ktkpos.frappe.cloud").rstrip("/")
API_KEY = os.getenv("ERPNEXT_API_KEY")
API_SECRET = os.getenv("ERPNEXT_API_SECRET")

def get_headers():
    return {
        "Authorization": f"token {API_KEY}:{API_SECRET}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def test_erpnext_connection():
    print("=" * 60)
    print("🚀 ERPNext 백엔드 연결 테스트 시작")
    print(f" - 대상 URL: {ERPNEXT_URL}")
    print(f" - API Key: {API_KEY[:4]}****" if API_KEY else " - API Key: 미설정")
    print("=" * 60)

    if not API_KEY or not API_SECRET:
        print("❌ [.env] ERPNEXT_API_KEY 또는 ERPNEXT_API_SECRET이 누락되었습니다.")
        return False

    headers = get_headers()

    # 1. 로그인 사용자 확인
    print("\n1. 현재 API 계정 정보 확인 (frappe.auth.get_logged_user)...")
    try:
        user_url = f"{ERPNEXT_URL}/api/method/frappe.auth.get_logged_user"
        res = requests.get(user_url, headers=headers, timeout=10)
        if res.status_code == 200:
            user_data = res.json()
            print(f"✅ 인증 성공! 로그인 사용자: {user_data.get('message', user_data)}")
        else:
            print(f"❌ 인증 실패 (HTTP {res.status_code}): {res.text}")
            return False
    except Exception as e:
        print(f"❌ 요청 오류: {e}")
        return False

    # 2. 품목(Item) 목록 조회 테스트
    print("\n2. 품목(Item) 목록 조회 테스트 (최근 5건)...")
    try:
        item_url = f"{ERPNEXT_URL}/api/resource/Item?fields=[\"name\",\"item_name\",\"item_group\",\"stock_uom\"]&limit_page_length=5"
        res = requests.get(item_url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get("data", [])
            print(f"✅ 품목 조회 성공! (가져온 품목 수: {len(items)}개)")
            for item in items:
                print(f"   📦 [{item.get('name')}] {item.get('item_name')} (그룹: {item.get('item_group')})")
        else:
            print(f"❌ 품목 조회 실패 (HTTP {res.status_code}): {res.text}")
    except Exception as e:
        print(f"❌ 품목 조회 오류: {e}")

    # 3. 창고(Warehouse) 목록 조회 테스트
    print("\n3. 창고(Warehouse) 목록 조회 테스트...")
    try:
        wh_url = f"{ERPNEXT_URL}/api/resource/Warehouse?fields=[\"name\",\"warehouse_name\",\"company\"]&limit_page_length=5"
        res = requests.get(wh_url, headers=headers, timeout=10)
        if res.status_code == 200:
            warehouses = res.json().get("data", [])
            print(f"✅ 창고 조회 성공! (가져온 창고 수: {len(warehouses)}개)")
            for wh in warehouses:
                print(f"   🏢 [{wh.get('name')}] {wh.get('warehouse_name')}")
        else:
            print(f"❌ 창고 조회 실패 (HTTP {res.status_code}): {res.text}")
    except Exception as e:
        print(f"❌ 창고 조회 오류: {e}")

    print("\n" + "=" * 60)
    print("🎉 ERPNext 연결 테스트가 정상적으로 완료되었습니다!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_erpnext_connection()
