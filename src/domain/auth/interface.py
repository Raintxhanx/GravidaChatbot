from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from src.data.models.users import UserModel

class IAuth(ABC):
    @abstractmethod
    def login(self, email: str, password: str) -> Optional[UserModel]:
        pass