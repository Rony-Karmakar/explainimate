import redis
import json
import os

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

def create_session(session_id: str):
    session = {
        "generated_code": None,
        "video_path": None,
        "plan": None,
        "version": 0,
        "versions": []
    }
    r.setex(
        session_id,
        86400,
        json.dumps(session)
    )
    return session

def get_session(session_id: str):
    data = r.get(session_id)
    if not data:
        return None
    return json.loads(data)

def update_session(session_id: str, updates: dict):
    session = get_session(session_id)
    if not session:
        return None
    session.update(updates)
    r.setex(
        session_id,
        86400,
        json.dumps(session)
    )

def delete_session(session_id: str):
    r.delete(session_id)