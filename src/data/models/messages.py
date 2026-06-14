import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from src.data.models.base import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

def generate_message_id():
    return str(uuid.uuid4())

class MessageModel(Base):
    __tablename__ = "messages"

    # ID menggunakan String untuk format custom [user_id]_[chat_id]_[increment]
    id = Column(String, primary_key=True, index=True, default=generate_message_id)
    chat_id = Column(String, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False) # 'system', 'user', atau 'assistant'
    
    # Menggunakan tipe data JSON (PostgreSQL otomatis mendukung pencarian di dalam JSONB)
    hidden_context = Column(JSON, nullable=True) # Instruksi RAG di balik layar
    content = Column(JSON, nullable=False) # Struktur chat utama atau teks
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True) # Index ditambahkan untuk sorting history yang cepat

    # Relasi balik ke Chat
    chat = relationship("ChatModel", back_populates="messages")