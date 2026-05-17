from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models import User
from services.auth_service import AuthService, decode_token
from services.business_error import BusinessError

_bearer = HTTPBearer()
_auth_service = AuthService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    """Dépendance FastAPI : extrait et valide le JWT, retourne l'utilisateur connecté."""
    payload = decode_token(credentials.credentials)

    user_id = payload.get("sub")
    if user_id is None:
        raise BusinessError("Token malformé", status_code=401)

    user = _auth_service.get_user_by_id(int(user_id))
    if user is None:
        raise BusinessError("Utilisateur introuvable", status_code=401)

    return user
