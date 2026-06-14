from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# --- Base Schema (Field yang sering dipakai bersama) ---
class CollectionBase(BaseModel):
    name: str = Field(..., description="Nama dari collection")
    is_active: Optional[bool] = True

# --- DTO untuk Create (Input) ---
class CollectionCreateDTO(CollectionBase):
    pass

# --- DTO untuk Query / Filter (Input) ---
class CollectionGetDTO(BaseModel):
    search: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    skip: int = Field(0, ge=0)

# --- DTO untuk Response (Output) ---
class CollectionResponseDTO(CollectionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        # Mengizinkan Pydantic membaca data langsung dari objek SQLAlchemy (CollectionModel)
        from_attributes = True