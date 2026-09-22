from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    consent_version: Mapped[str] = mapped_column(String(32), default="2026-09-21")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MessageEdit(Base):
    __tablename__ = "message_edits"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    old_content: Mapped[str] = mapped_column(Text())
    new_content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Rating(Base):
    __tablename__ = "ratings"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AdapterRelease(Base):
    __tablename__ = "adapter_releases"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    config_json: Mapped[str] = mapped_column(Text())
    source_message_count: Mapped[int] = mapped_column(Integer(), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

def init_db() -> None:
    if settings.database_url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(engine)

def ensure_conversation(db: Session, conversation_id: str) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        conversation = Conversation(id=conversation_id)
        db.add(conversation)
        db.commit()
    return conversation

def get_messages(db: Session, conversation_id: str, limit: int = 30) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(reversed(db.scalars(stmt).all()))

def add_message(db: Session, conversation_id: str, role: str, content: str) -> Message:
    message = Message(id=str(uuid.uuid4()), conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    db.commit()
    return message

def add_rating(db: Session, conversation_id: str, message_id: str, rating: int) -> None:
    if rating not in (1, 2, 3, 4, 5):
        raise ValueError("rating must be between 1 and 5")
    message = db.get(Message, message_id)
    if message is None or message.conversation_id != conversation_id:
        raise ValueError("message not found")
    db.add(Rating(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        message_id=message_id,
        rating=rating,
    ))
    db.commit()

def delete_conversation(db: Session, conversation_id: str) -> None:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        return
    for row in db.scalars(select(MessageEdit).where(MessageEdit.conversation_id == conversation_id)).all():
        db.delete(row)
    for row in db.scalars(select(Rating).where(Rating.conversation_id == conversation_id)).all():
        db.delete(row)
    for row in db.scalars(select(Message).where(Message.conversation_id == conversation_id)).all():
        db.delete(row)
    db.delete(conversation)
    db.commit()

def edit_message(db: Session, conversation_id: str, message_id: str, new_content: str) -> Message:
    message = db.get(Message, message_id)
    if message is None or message.conversation_id != conversation_id:
        raise ValueError("message not found")
    old = message.content
    message.content = new_content
    db.add(MessageEdit(
        id=str(uuid.uuid4()),
        message_id=message_id,
        conversation_id=conversation_id,
        old_content=old,
        new_content=new_content,
    ))
    db.commit()
    return message

def latest_adapter(db: Session) -> dict[str, Any]:
    row = db.scalars(select(AdapterRelease).order_by(AdapterRelease.created_at.desc()).limit(1)).first()
    if row is None:
        return {
            "version": "bootstrap",
            "system_addendum": "Be helpful, clear, warm, and natural. Match the user's requested level of detail without overdoing it.",
            "signals": {},
        }
    payload = json.loads(row.config_json)
    payload["version"] = row.version
    return payload
