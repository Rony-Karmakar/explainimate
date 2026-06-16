from pydantic import BaseModel
from typing import Optional

class GenerateRequest(BaseModel):
    prompt: str

class FeedbackRequest(BaseModel):
    session_id: str
    feedback: str

class GenerateResponse(BaseModel):
    session_id: str
    video_path: str
    version: int
    message: str

class VersionResponse(BaseModel):
    version: int
    feedback: str
    video_path: str