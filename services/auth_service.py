from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from database import DuplicateError
from database.repositories.user_repository import UserRepository
from models import User
from services.business_error import BusinessError
from utils import ModelMapper

_user_repository = UserRepository()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Décode et valide un JWT. Lève BusinessError si invalide."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise BusinessError("Token invalide ou expiré", status_code=401)


class AuthService:
    def register(self, email: str, password: str) -> User:
        if len(password) < 8:
            raise BusinessError("Le mot de passe doit contenir au moins 8 caractères")

        try:
            user_id = _user_repository.create(
                email=email.lower().strip(),
                password_hash=_hash_password(password),
            )
        except DuplicateError:
            raise BusinessError("Un compte avec cet email existe déjà", status_code=409)

        row = _user_repository.find_by({"id": user_id})[0]
        return ModelMapper.to_model(User, row)

    def login(self, email: str, password: str) -> str:
        row = _user_repository.find_by_email(email.lower().strip())
        if row is None or not _verify_password(password, row["password_hash"]):
            raise BusinessError("Email ou mot de passe incorrect", status_code=401)

        user = ModelMapper.to_model(User, row)
        return _create_access_token(user.id, user.email)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        rows = _user_repository.find_by({"id": user_id})
        return ModelMapper.to_model(User, rows[0]) if rows else None
