import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

# Import Interface dan DTO (Sesuaikan path import dengan struktur project Anda)
from src.domain.collection.interface import ICollection
from src.data.models.collections import CollectionModel
from src.data.repo.qdrant import QdrantRepository

from src.domain.collection.model import (
    CollectionCreateDTO,
    CollectionGetDTO,
    CollectionResponseDTO
)

logger = logging.getLogger(__name__)

class CollectionUseCases(ICollection):
    """
    Use Case layer untuk manajemen data Collection menggunakan SQLAlchemy Session langsung.
    Orchestrating business logic, single-active rule enforcement, dan direct database interaction.
    """
    def __init__(self, db: Session, qdrant_repo: QdrantRepository):
        self._db = db
        self._qdrant = qdrant_repo

    def create(self, model: CollectionCreateDTO) -> CollectionResponseDTO:
        logger.info(f"[COLLECTION USE CASE] Mencoba membuat collection dengan nama: {model.name}")
        
        # 1. Validasi Bisnis
        existing_collection = self._db.query(CollectionModel).filter(CollectionModel.name == model.name).first()
        if existing_collection:
            logger.warning(f"[COLLECTION USE CASE] Gagal membuat collection: Nama {model.name} sudah terdaftar")
            raise ValueError("Nama collection sudah terdaftar")

        try:
            # 2. Mapping & Business Rules Handling
            collection_data = model.model_dump()
            
            # Jika collection baru diset aktif, matikan yang sebelumnya aktif
            if collection_data.get("is_active", True):
                active_collections = self._db.query(CollectionModel).filter(CollectionModel.is_active == True).all()
                for active_col in active_collections:
                    active_col.is_active = False

            new_collection = CollectionModel(**collection_data)

            try:
                self._qdrant.ensure_collection(collection_name=model.name)

                logger.info(
                    f"[COLLECTION USE CASE] Collection Qdrant '{model.name}' berhasil dibuat/divalidasi"
                )

            except Exception as qdrant_error:
                logger.error(
                    f"[COLLECTION USE CASE] Gagal membuat collection Qdrant '{model.name}': {str(qdrant_error)}",
                    exc_info=True,
                )

                raise ValueError(
                    f"Gagal membuat collection di Qdrant: {str(qdrant_error)}"
                )            
            
            self._db.add(new_collection)
            self._db.commit()
            self._db.refresh(new_collection)
            
            return CollectionResponseDTO.model_validate(new_collection)
            
        except Exception as e:
            self._db.rollback()
            logger.error(f"[COLLECTION USE CASE] Gagal sistem saat membuat collection: {e}", exc_info=True)
            raise e

    def delete(self, id: UUID) -> CollectionResponseDTO:
        logger.info(f"[COLLECTION USE CASE] Menghapus collection ID: {id}")
        
        collection = self._db.query(CollectionModel).filter(CollectionModel.id == id).first()
        if not collection:
            logger.warning(f"[COLLECTION USE CASE] Gagal menghapus: Collection {id} tidak ditemukan")
            raise ValueError("Collection tidak ditemukan")

        try:
            # Sesuai kontrak interface, return DTO dari data yang dihapus
            response_dto = CollectionResponseDTO.model_validate(collection)
            
            # Catatan: Hanya menghapus di database apps saja (bukan di Qdrant)
            self._db.delete(collection)
            self._db.commit()
            
            return response_dto
        except Exception as e:
            self._db.rollback()
            logger.error(f"[COLLECTION USE CASE] Gagal sistem saat menghapus collection {id}: {e}", exc_info=True)
            raise e

    def active(self, id: UUID) -> CollectionResponseDTO:
        logger.info(f"[COLLECTION USE CASE] Mengaktifkan/menyetel aktif untuk collection ID: {id}")
        
        collection = self._db.query(CollectionModel).filter(CollectionModel.id == id).first()
        if not collection:
            logger.warning(f"[COLLECTION USE CASE] Gagal mengaktifkan: Collection {id} tidak ditemukan")
            raise ValueError("Collection tidak ditemukan")

        try:
            # Aturan bisnis: Hanya boleh ada 1 yang aktif. Loop untuk mematikan yang aktif sebelumnya
            active_collections = self._db.query(CollectionModel).filter(CollectionModel.is_active == True).all()
            for active_col in active_collections:
                active_col.is_active = False
            
            # Aktifkan yang dipilih
            collection.is_active = True
            
            self._db.commit()
            self._db.refresh(collection)
            
            return CollectionResponseDTO.model_validate(collection)
        except Exception as e:
            self._db.rollback()
            logger.error(f"[COLLECTION USE CASE] Gagal sistem saat mengaktifkan collection {id}: {e}", exc_info=True)
            raise e

    def get_active(self) -> CollectionResponseDTO:
        logger.info(f"[COLLECTION USE CASE] Mengambil data collection yang sedang aktif")
        
        collection = self._db.query(CollectionModel).filter(CollectionModel.is_active == True).first()
        if not collection:
            logger.warning(f"[COLLECTION USE CASE] Gagal mengambil: Tidak ada collection yang aktif")
            raise ValueError("Tidak ada collection yang aktif")
            
        return CollectionResponseDTO.model_validate(collection)

    def get_all(self, model: CollectionGetDTO) -> List[CollectionResponseDTO]:
        logger.info(f"[COLLECTION USE CASE] Mengambil list collection dengan filter")
        try:
            # Inisialisasi base query
            query_obj = self._db.query(CollectionModel)

            # ── Dynamic Filtering ─────────────────────────────────────────────
            if model.search:
                # Search parsial (case-insensitive) pada kolom nama
                search_filter = f"%{model.search}%"
                query_obj = query_obj.filter(CollectionModel.name.ilike(search_filter))

            # ── Pagination ────────────────────────────────────────────────────
            collections = query_obj.offset(model.skip).limit(model.limit).all()
            
            return [CollectionResponseDTO.model_validate(col) for col in collections]
        
        except Exception as e:
            logger.error(f"[COLLECTION USE CASE] Gagal mengambil list collection: {e}", exc_info=True)
            raise e