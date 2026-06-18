import redis
import json
import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("DATABASE_URL")

if not url:
    raise ValueError("DATABASE_URL is not set in .env")

engine = create_engine(url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class VideoHistory(Base):
    __tablename__ = "video_history"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    version = Column(Integer)
    prompt = Column(Text)
    feedback = Column(Text, nullable=True)
    video_path = Column(String)
    code = Column(Text)
    created_at = Column(DateTime, default=datetime.time)

Base.metadata.create_all(engine)

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