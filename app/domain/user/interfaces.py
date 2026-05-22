from abc import ABC, abstractmethod
import uuid
from app.domain.user.entities import User
from typing import Optional

class IUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def save(self, user: User, password_hash: str) -> User:
        pass

    @abstractmethod
    def update_last_login(self, user_id: uuid.UUID):
        pass