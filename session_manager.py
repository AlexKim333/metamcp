import time
from typing import Dict, Any, List

# 접속자별 세션 히스토리 캐시
# key: user_id (전화번호 또는 텔레그램 chat_id)
# value: {"recent_items": ["P-160-NEGRO-400", "021G-AZUL-400"], "last_queried_at": float}
_USER_SESSIONS: Dict[str, Dict[str, Any]] = {}

def record_queried_item(user_id: str, item_code: str):
    """사용자가 조회한 품목 코드를 세션 히스토리에 기록 (최대 10개 FIFO)"""
    if not user_id or not item_code:
        return

    clean_id = str(user_id).strip()
    clean_code = str(item_code).strip()

    if clean_id not in _USER_SESSIONS:
        _USER_SESSIONS[clean_id] = {
            "recent_items": [],
            "last_queried_at": time.time()
        }

    session = _USER_SESSIONS[clean_id]
    recent = session["recent_items"]

    # 중복 제거 후 맨 뒤에 추가
    if clean_code in recent:
        recent.remove(clean_code)
    recent.append(clean_code)

    # 최대 10개 유지
    if len(recent) > 10:
        session["recent_items"] = recent[-10:]
    session["last_queried_at"] = time.time()

def get_recent_queried_items(user_id: str) -> List[str]:
    """사용자가 최근에 조회했던 품목 코드 목록 반환"""
    clean_id = str(user_id).strip()
    if clean_id in _USER_SESSIONS:
        return _USER_SESSIONS[clean_id].get("recent_items", [])
    return []

def clear_user_session_items(user_id: str):
    """전표 생성 완료 후 세션 큐 초기화"""
    clean_id = str(user_id).strip()
    if clean_id in _USER_SESSIONS:
        _USER_SESSIONS[clean_id]["recent_items"] = []
