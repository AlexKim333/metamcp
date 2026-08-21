import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def test_gemini_connection():
    print("=" * 60)
    print("🤖 Gemini API 연결 및 텍스트 생성 테스트 시작")
    print(f" - API Key: {GEMINI_API_KEY[:8]}****" if GEMINI_API_KEY else " - API Key: 미설정")
    print("=" * 60)

    if not GEMINI_API_KEY:
        print("❌ [.env] GEMINI_API_KEY가 설정되지 않았습니다.")
        return False

    prompt = "ERPNext WMS 시스템과 WhatsApp을 연동하는 AI 어시스턴트입니다. 한 문장으로 간단히 인사해줘."
    
    # 신규 google.genai SDK 사용
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 모델 테스트 (gemini-3.6-flash 또는 gemini-2.0-flash / gemini-2.5-flash 등 지원 모델 자동 시도)
        candidate_models = ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
        for m in candidate_models:
            try:
                print(f"🔄 모델 [{m}] 호출 시도 중...")
                response = client.models.generate_content(
                    model=m,
                    contents=prompt
                )
                print(f"✅ Gemini GenAI SDK ({m}) 호출 성공!")
                print(f"💬 응답 내용:\n{response.text.strip()}")
                return True
            except Exception as model_err:
                print(f"   ⚠️ {m} 실패: {model_err}")
                
        return False
    except Exception as e:
        print(f"❌ Google GenAI SDK 오류: {e}")
        return False

if __name__ == "__main__":
    test_gemini_connection()
