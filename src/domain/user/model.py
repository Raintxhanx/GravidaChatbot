from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

# --- Base Schema (Field yang sering dipakai bersama) ---
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    domicile: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = "user"
    estimated_delivery_date: Optional[date] = None
    pregnancy_count: Optional[int] = Field(None, ge=0)
    medical_history: Optional[str] = None

# --- DTO untuk Create (Input) ---
class UserCreateDTO(UserBase):
    password: str = Field(..., min_length=8, description="Password polos dari user sebelum di-hash")
    
    # Menimpa (Override) field agar WAJIB diisi saat endpoint /register dipanggil
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=120)
    domicile: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=1)
    
    # Data spesifik kehamilan yang wajib saat daftar
    estimated_delivery_date: date 
    pregnancy_count: int = Field(..., ge=0)

# --- DTO untuk Update (Input) ---
# Semua dibuat opsional agar mendukung partial update (PATCH style)
class UserUpdateDTO(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    domicile: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None
    estimated_delivery_date: Optional[date] = None
    pregnancy_count: Optional[int] = Field(None, ge=0)
    medical_history: Optional[str] = None

# --- DTO untuk Query / Filter (Input) ---
class UserGetDTO(BaseModel):
    search: Optional[str] = None
    domicile: Optional[str] = None
    role: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    skip: int = Field(0, ge=0)

# --- DTO untuk Response (Output) ---
class UserResponseDTO(UserBase):
    id: UUID
    created_at: datetime
    last_active: Optional[datetime] = None

    class Config:
        # Mengizinkan Pydantic membaca data langsung dari objek SQLAlchemy (UserModel)
        from_attributes = True