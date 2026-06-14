from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from src.domain.user.model import UserCreateDTO, UserUpdateDTO, UserGetDTO, UserResponseDTO

class IUser(ABC):
    
    @abstractmethod
    def create(self, model: UserCreateDTO) -> UserResponseDTO:
        pass

    @abstractmethod
    def update(self, id: UUID, model: UserUpdateDTO) -> UserResponseDTO:
        # Ditambahkan 'id' agar tahu user mana yang mau diupdate
        pass

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        # Ditambahkan return type (misal: bool untuk penanda berhasil/gagal)
        pass

    @abstractmethod
    def get(self, id: UUID) -> Optional[UserResponseDTO]:
        # Mengambil single user biasanya lebih efisien via ID langsung
        pass

    @abstractmethod
    def get_all(self, query: UserGetDTO) -> List[UserResponseDTO]:
        pass

    @abstractmethod
    def update_last_login(self, id: UUID) -> UserResponseDTO:
        pass