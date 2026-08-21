import os
import sys
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
API_VERSION = os.getenv("META_API_VERSION", "v19.0")
APP_ID = "1063068856264071" # WABA ID 또는 App ID

def update_whatsapp_profile():
    img_path = os.path.join(os.path.dirname(__file__), "samdori-icon.jpg")
    if not os.path.exists(img_path):
        print(f"❌ 이미지 파일이 없습니다: {img_path}")
        return False

    file_size = os.path.getsize(img_path)
    print(f"🖼️ 삼돌이 프로필 이미지 업로드 시작 (크기: {file_size:,} bytes)...")

    # 1. Resumable Upload 세션 생성
    url_upload_session = f"https://graph.facebook.com/{API_VERSION}/app/uploads"
    params = {
        "file_length": file_size,
        "file_type": "image/jpeg",
        "access_token": ACCESS_TOKEN
    }

    try:
        res = requests.post(url_upload_session, params=params, timeout=15)
        data = res.json()
        upload_session_id = data.get("id")
        
        if not upload_session_id:
            print(f"⚠️ 세션 생성 실패: {data}")
            return False

        print(f"✅ 업로드 세션 생성 완료: {upload_session_id}")

        # 2. 이미지 바이너리 전송
        with open(img_path, "rb") as f:
            img_data = f.read()

        upload_url = f"https://graph.facebook.com/{API_VERSION}/{upload_session_id}"
        headers = {
            "Authorization": f"OAuth {ACCESS_TOKEN}",
            "file_offset": "0"
        }
        
        res_upload = requests.post(upload_url, headers=headers, data=img_data, timeout=30)
        upload_res_data = res_upload.json()
        handle = upload_res_data.get("h")

        if not handle:
            print(f"⚠️ 파일 핸들 획득 실패: {upload_res_data}")
            return False

        print(f"✅ 파일 핸들 획득 완료: {handle}")

        # 3. WhatsApp 비즈니스 프로필 사진 업데이트
        profile_url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/whatsapp_business_profile"
        headers_profile = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        profile_payload = {
            "messaging_product": "whatsapp",
            "profile_picture_handle": handle,
            "about": "ladypolo AI 비서 (재고/물류 관리)",
            "description": "ladypolo 실시간 재고 조회 및 물류 관리 AI 어시스턴트입니다."
        }

        res_profile = requests.post(profile_url, headers=headers_profile, json=profile_payload, timeout=15)
        print(f"Profile Update Response ({res_profile.status_code}): {res_profile.json()}")

        if res_profile.status_code == 200:
            print("🎉 삼돌이 프로필 이미지 및 비즈니스 소개글 업데이트 성공!")
            return True
        else:
            print("❌ 프로필 업데이트 실패")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    update_whatsapp_profile()
