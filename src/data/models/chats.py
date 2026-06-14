import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from src.data.models.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class ChatModel(Base):
    __tablename__ = "chats"

    # ID menggunakan String karena format custom akan di-generate di layer services
    id = Column(String, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True) # Aman dari SQL reserved keyword
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relasi (Optional, mempermudah query back-reference)
    messages = relationship("MessageModel", back_populates="chat", cascade="all, delete-orphan")