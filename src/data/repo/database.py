import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from src.data.models.base import Base
from src.data.models.users import UserModel
from src.data.models.chats import ChatModel
from src.data.models.messages import MessageModel
from src.data.models.collections import CollectionModel
from src.data.models.settings import SettingModel

class Database:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def init_db(self):
        """Membuat semua tabel di database jika belum ada"""
        Base.metadata.create_all(bind=self.engine) 

    def populate_admin(self, db_session, password_service, admin_password):
        try:
            admin_email = "admin@raintxhanx.com"
            # Cek apakah admin sudah ada di database
            existing_admin = db_session.query(UserModel).filter_by(email=admin_email).first()

            if not existing_admin:
                hashed_password = password_service.hash_password(admin_password)
                new_admin = UserModel(
                    email=admin_email,
                    hash_password=hashed_password,
                    role="admin"
                )
                db_session.add(new_admin)
                db_session.commit()
                logging.info("Berhasil: Akun Admin default telah dibuat.")
            else:
                logging.info("Info: Akun Admin sudah ada di database (Skip populate).")
                
        except Exception as e:
            db_session.rollback()
            logging.error(f"Gagal saat mencoba populate admin: {e}")
            raise e