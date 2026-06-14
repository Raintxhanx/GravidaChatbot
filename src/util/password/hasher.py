import bcrypt
import logging

logger = logging.getLogger(__name__)

class PasswordHasher:
    """
    Service utility untuk manajemen keamanan password.
    Menggunakan algoritma Bcrypt untuk proses hashing dan verifikasi.
    """

    def hash_password(self, password: str) -> str:
        """
        Mengubah password polos (plaintext) menjadi hash yang aman.
        """
        if not password:
            raise ValueError("Password tidak boleh kosong")

        try:
            # Bcrypt menerima inputan dalam bentuk bytes, lakukan encoding
            password_bytes = password.encode('utf-8')
            
            # Generate salt dan lakukan hashing
            salt = bcrypt.gensalt()
            hashed_bytes = bcrypt.hashpw(password_bytes, salt)
            
            # Kembalikan dalam bentuk string (utf-8) agar cocok dengan tipe data String/VARCHAR di DB
            return hashed_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"[PASSWORD HASHER] Gagal melakukan enkripsi password: {e}")
            raise RuntimeError("Gagal memproses password")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Memvalidasi apakah password polos cocok dengan hash yang disimpan di database.
        Digunakan nanti pada proses Auth / Login.
        """
        if not password or not hashed_password:
            return False

        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # Bcrypt.checkpw akan mengekstrak salt dari hashed_bytes secara otomatis
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"[PASSWORD HASHER] Gagal memverifikasi password: {e}")
            return False