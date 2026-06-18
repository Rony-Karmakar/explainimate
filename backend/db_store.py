# db_store.py
from store import SessionLocal, VideoHistory

def save_video(session_id, version, prompt, feedback, video_path, code):
    db = SessionLocal()
    try:
        record = VideoHistory(
            session_id=session_id,
            version=version,
            prompt=prompt,
            feedback=feedback,
            video_path=video_path,
            code=code
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

def get_video_history(session_id):
    db = SessionLocal()
    try:
        return db.query(VideoHistory)\
                 .filter(VideoHistory.session_id == session_id)\
                 .order_by(VideoHistory.version)\
                 .all()
    finally:
        db.close()

def get_all_videos():
    db = SessionLocal()
    try:
        return db.query(VideoHistory)\
                 .order_by(VideoHistory.created_at.desc())\
                 .all()
    finally:
        db.close()