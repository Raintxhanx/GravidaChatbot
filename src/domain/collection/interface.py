from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from src.domain.collection.model import CollectionCreateDTO, CollectionGetDTO, CollectionResponseDTO

class ICollection(ABC):
    @abstractmethod
    def create(self, model: CollectionCreateDTO) -> CollectionResponseDTO:
        pass

    @abstractmethod
    #delete hanya bisa menghapus di database apps aja.. bukan di apps qdrant
    def delete(self, id: UUID) -> CollectionResponseDTO:
        pass

    @abstractmethod
    #hanya akan ada 1 collection yang aktif.. buat jaga2.. setiap kali aktifkan collection.. buat loop untuk matikan yang active sebelumnya
    def active(self, id: UUID) -> CollectionResponseDTO:
        pass

    @abstractmethod
    def get_active(self) -> CollectionResponseDTO:
        pass

    @abstractmethod
    def get_all(self, model: CollectionGetDTO) -> List[CollectionResponseDTO]:
        pass