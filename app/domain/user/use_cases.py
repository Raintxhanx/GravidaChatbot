import jwt
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.data.models.user import UserModel
from app.domain.user.interfaces import IUserRepository

class UserUseCase:
    def __init__(self, repo: IUserRepository, secret_key: str):
        self.repo = repo
        self.secret_key = secret_key

    def register(self, email, password, role='user'):
        if self.repo.get_by_email(email):
            return None, "Email already exists"
        
        from app.domain.user.entities import User
        hashed_pw = generate_password_hash(password)
        user_entity = User(email=email, role=role)
        return self.repo.save(user_entity, hashed_pw), "Success"

    def login(self, email, password):
        user_db = UserModel.query.filter_by(email=email).first()
        if user_db and check_password_hash(user_db.password_hash, password):
            # PERBAIKAN DI SINI
            token = jwt.encode({
                'user_id': str(user_db.id),
                'role': user_db.role,
                # Gunakan datetime.now(timezone.utc) untuk Python 3.12+
                'exp': datetime.now(timezone.utc) + timedelta(hours=24)
            }, self.secret_key, algorithm="HS256")
            
            self.repo.update_last_login(user_db.id)
            return token, user_db.to_entity()
        return None, "Invalid credentials"