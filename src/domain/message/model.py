from pydantic import BaseModel, Field
from typing import Any, Optional, List
from uuid import UUID
from datetime import datetime

# ==========================================
# Message DTOs
# ==========================================

class MessageUpdateDTO(BaseModel):
    """Digunakan saat melakukan regenerate atau menyunting pesan"""
    query: str = Field(..., description="Pesan user baru atau lama yang ingin di-regenerate")


class MessageResponseDTO(BaseModel):
    id: str
    chat_id: str
    role: str
    hidden_context: Optional[Any] = None
    content: Any
    created_at: datetime

    class Config:
        from_attributes = True

class MessageGetAllDTO(BaseModel):
    search: Optional[str] = None
    before_message_id: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)

class MessageListResponseDTO(BaseModel):
    items: List[MessageResponseDTO]
    next_cursor: Optional[str] = None
    has_more: bool = False