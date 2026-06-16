from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import json
from agent import run_agent
from models import GenerateRequest

app = FastAPI(title="Explainimate API")

# ── CORS ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = {}

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Explainimate API"}

@app.post("/generate")
def generate_video(data: GenerateRequest):
    res = run_agent(data.prompt)
    
    return {"status": "ok", "video": res}