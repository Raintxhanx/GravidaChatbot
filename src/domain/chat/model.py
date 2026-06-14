from pydantic import BaseModel, Field
from typing import Any, Optional, List
from uuid import UUID
from datetime import datetime

# ==========================================
# Chat Session DTOs
# ==========================================

class ChatUpdateDTO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ChatResponseDTO(BaseModel):
    id: str
    user_id: UUID
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatGetAllDTO(BaseModel):
    search: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    skip: int = Field(0, ge=0)
    start_date: Optional[datetime] = None  # Diubah menjadi opsional
    end_date: Optional[datetime] = None    # Menggantikan duplikasi start_date sebelumny