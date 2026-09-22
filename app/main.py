from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .adapter import get_global_personality
from .database import (
    SessionLocal,
    add_message,
    add_rating,
    delete_conversation,
    edit_message,
    ensure_conversation,
    get_messages,
    init_db,
)
from .llm import generate

app = FastAPI(title="Global Personality Chatbot", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup() -> None:
    init_db()

def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1, max_length=12000)
    consent: bool

class RatingRequest(BaseModel):
    conversation_id: str
    message_id: str
    rating: int = Field(ge=1, le=5)

class EditRequest(BaseModel):
    conversation_id: str
    message_id: str
    new_content: str = Field(min_length=1, max_length=12000)

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/chat")
async def chat(req: ChatRequest, db: Session = Depends(db_session)):
    if not req.consent:
        raise HTTPException(status_code=400, detail="Consent is required before messages can be stored or used for tuning.")

    ensure_conversation(db, req.conversation_id)
    user_msg = add_message(db, req.conversation_id, "user", req.message)
    history = get_messages(db, req.conversation_id)
    llm_messages = [{"role": m.role, "content": m.content} for m in history]

    try:
        adapter = get_global_personality(db)
        reply = await generate(llm_messages, adapter)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM backend unavailable: {exc}") from exc

    assistant_msg = add_message(db, req.conversation_id, "assistant", reply)
    return {
        "user_message_id": user_msg.id,
        "message_id": assistant_msg.id,
        "reply": reply,
        "adapter_version": adapter.get("version", "bootstrap"),
    }

@app.post("/api/rating")
def rate(req: RatingRequest, db: Session = Depends(db_session)):
    try:
        add_rating(db, req.conversation_id, req.message_id, req.rating)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}

@app.post("/api/edit")
def edit(req: EditRequest, db: Session = Depends(db_session)):
    try:
        message = edit_message(db, req.conversation_id, req.message_id, req.new_content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "message_id": message.id, "content": message.content}

@app.get("/api/conversations/{conversation_id}")
@app.delete("/api/conversations/{conversation_id}")
def delete_conversation_route(conversation_id: str, db: Session = Depends(db_session)):
    delete_conversation(db, conversation_id)
    return {"ok": True}

@app.get("/api/conversations/{conversation_id}")
def conversation(conversation_id: str, db: Session = Depends(db_session)):
    return {
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content}
            for m in get_messages(db, conversation_id, limit=100)
        ]
    }
