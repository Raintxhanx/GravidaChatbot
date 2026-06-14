import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Import Interface dan DTO
from src.domain.auth.interface import IAuth
from src.util.password.hasher import PasswordHasher 
from src.data.models.users import UserModel

logger = logging.getLogger(__name__)

class AuthUseCases(IAuth):
    def __init__(self, db: Session, password_service: PasswordHasher):
        self._db = db
        self._password_service = password_service

    def login(self, email: str, password: str) -> Optional[UserModel]:
        logger.info(f"[USER USE CASE] Memproses login untuk email: {email}")
        try:
            # Cari user berdasarkan email
            user = self._db.query(UserModel).filter(UserModel.email == email).first()
            if not user:
                logger.warning(f"[USER USE CASE] Login gagal: Email {email} tidak ditemukan")
                return None
            
            # Verifikasi password polos dengan hash di DB
            if not self._password_service.verify_password(password, user.hash_password):
                logger.warning(f"[USER USE CASE] Login gagal: Password salah untuk email {email}")
                return None
            
            # Update timestamp login terakhir
            user.last_active = datetime.now(timezone.utc)
            self._db.commit()
            self._db.refresh(user)
            
            return user
        except Exception as e:
            self._db.rollback()
            logger.error(f"[USER USE CASE] Terjadi kesalahan saat proses login: {e}")
            raise e

    