from app.domain.user.interfaces import IUserRepository
from app.domain.user.entities import User
from app.data.models.user import db, UserModel
from typing import Optional
from datetime import datetime, timezone
import uuid


class SQLUserRepository(IUserRepository):
    def get_by_email(self, email: str) -> Optional[User]:
        user_db = UserModel.query.filter_by(email=email).first()
        return user_db.to_entity() if user_db else None

    def save(self, user_entity: User, password_hash: str) -> User:
        new_user = UserModel(
            email=user_entity.email,
            password_hash=password_hash,
            role=user_entity.role,
            profile_picture=user_entity.profile_picture
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user.to_entity()

    def update_last_login(self, user_id: uuid.UUID):
        user = UserModel.query.get(user_id)
        if user:
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()