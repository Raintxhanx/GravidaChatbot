import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Import Interface dan DTO
from src.domain.user.interface import IUser
from src.util.password.hasher import PasswordHasher 
from src.data.models.users import UserModel

from src.domain.user.model import (
    UserCreateDTO, 
    UserUpdateDTO, 
    UserGetDTO, 
    UserResponseDTO
)

logger = logging.getLogger(__name__)

class UserUseCases(IUser):
    """
    Use Case layer untuk manajemen data User menggunakan SQLAlchemy Session langsung.
    Orchestrating business logic, password hashing, dan direct database interaction.
    """
    def __init__(self, db: Session, password_service: PasswordHasher):
        self._db = db
        self._password_service = password_service

    def create(self, model: UserCreateDTO) -> UserResponseDTO:
        logger.info(f"[USER USE CASE] Mencoba membuat user dengan email: {model.email}")
        
        existing_user = self._db.query(UserModel).filter(UserModel.email == model.email).first()
        if existing_user:
            logger.warning(f"[USER USE CASE] Gagal membuat user: Email {model.email} sudah terdaftar")
            raise ValueError("Email sudah terdaftar")

        try:
            hashed_password = self._password_service.hash_password(model.password)
            user_data = model.model_dump(exclude={"password"})
            
            # ── PAKSA ROLE SELALU USER ────────────────────────────────────────
            user_data["role"] = "user"
            user_data["hash_password"] = hashed_password

            new_user = UserModel(**user_data)
            
            self._db.add(new_user)
            self._db.commit()
            self._db.refresh(new_user)
            
            return UserResponseDTO.model_validate(new_user)
            
        except Exception as e:
            self._db.rollback()
            logger.error(f"[USER USE CASE] Gagal sistem saat membuat user: {e}", exc_info=True)
            raise e

    def update(self, id: UUID, model: UserUpdateDTO) -> UserResponseDTO:
        logger.info(f"[USER USE CASE] Memperbarui data user ID: {id}")
        
        user = self._db.query(UserModel).filter(UserModel.id == id).first()
        if not user:
            logger.warning(f"[USER USE CASE] Gagal memperbarui: User {id} tidak ditemukan")
            raise ValueError("User tidak ditemukan")

        try:
            update_data = model.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(user, key, value)
            
            self._db.commit()
            self._db.refresh(user)
            
            return UserResponseDTO.model_validate(user)
        except Exception as e:
            self._db.rollback()
            logger.error(f"[USER USE CASE] Gagal sistem saat memperbarui user {id}: {e}", exc_info=True)
            raise e

    def delete(self, id: UUID) -> bool:
        logger.info(f"[USER USE CASE] Menghapus user ID: {id}")
        
        user = self._db.query(UserModel).filter(UserModel.id == id).first()
        if not user:
            logger.warning(f"[USER USE CASE] Gagal menghapus: User {id} tidak ditemukan")
            raise ValueError("User tidak ditemukan") # Diubah menjadi raise agar konsisten dengan update

        try:
            self._db.delete(user)
            self._db.commit()
            return True
        except Exception as e:
            self._db.rollback()
            logger.error(f"[USER USE CASE] Gagal sistem saat menghapus user {id}: {e}", exc_info=True)
            raise e

    def get(self, id: UUID) -> Optional[UserResponseDTO]:
        logger.info(f"[USER USE CASE] Mengambil data user ID: {id}")
        user = self._db.query(UserModel).filter(UserModel.id == id).first()
        if not user:
            return None
        return UserResponseDTO.model_validate(user)

    def get_all(self, query: UserGetDTO) -> List[UserResponseDTO]:
        logger.info(f"[USER USE CASE] Mengambil list user dengan filter")
        try:
            # Inisialisasi base query
            query_obj = self._db.query(UserModel)

            # ── Dynamic Filtering ─────────────────────────────────────────────
            if query.domicile:
                query_obj = query_obj.filter(UserModel.domicile == query.domicile)
                
            if query.role:
                query_obj = query_obj.filter(UserModel.role == query.role)
                
            if query.search:
                # Search parsial (case-insensitive) pada kolom nama ATAU email
                search_filter = f"%{query.search}%"
                query_obj = query_obj.filter(
                    or_(
                        UserModel.name.ilike(search_filter),
                        UserModel.email.ilike(search_filter)
                    )
                )

            # ── Pagination ────────────────────────────────────────────────────
            users = query_obj.offset(query.skip).limit(query.limit).all()
            
            return [UserResponseDTO.model_validate(user) for user in users]
        
        except Exception as e:
            logger.error(f"[USER USE CASE] Gagal mengambil list user: {e}")
            raise e

    def update_last_login(self, id: UUID) -> UserResponseDTO:
        logger.info(f"[USER USE CASE] Memperbarui last active untuk user ID: {id}")
        try:
            user = self._db.query(UserModel).filter(UserModel.id == id).first()
            if not user:
                raise ValueError("User tidak ditemukan")
                
            current_time = datetime.now(timezone.utc)
            user.last_active = current_time
            
            self._db.commit()
            self._db.refresh(user)
            return UserResponseDTO.model_validate(user)
        
        except Exception as e:
            self._db.rollback()
            logger.error(f"[USER USE CASE] Gagal memperbarui login terakhir: {e}")
            raise e