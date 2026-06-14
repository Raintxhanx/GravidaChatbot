import uuid
from sqlalchemy import Column, String, Integer, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from src.data.models.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    domicile = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hash_password = Column(String, nullable=False)
    phone_number = Column(String, unique=True, nullable=True)
    role = Column(String, default="user") # 'admin' atau 'user'
    
    # Data Spesifik Kehamilan (Fitur RAG/AI Tone)
    estimated_delivery_date = Column(Date, nullable=True) # HPL
    pregnancy_count = Column(Integer, nullable=True) # Kehamilan ke-berapa
    medical_history = Column(String, nullable=True) # Menggunakan String/Text untuk riwayat medis
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True) # Tambahkan timezone=True # Tidak otomatis (diupdate manual via aplikasi)