from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from schemas.user_schema import (
    LoginRequest,
    RegisterRequest,
    SingleUserResponse,
    TokenData,
    TokenResponse,
    UserResponse,
)
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_service = AuthService()


def _json(model, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=model.model_dump(mode="json"), status_code=status_code)


@router.post("/register", summary="Créer un compte", response_model=SingleUserResponse, status_code=201)
def register(body: RegisterRequest):
    user = _service.register(email=body.email, password=body.password)
    return _json(SingleUserResponse(data=UserResponse.model_validate(user)), status_code=201)


@router.post("/login", summary="Se connecter (obtenir un JWT)", response_model=TokenResponse)
def login(body: LoginRequest):
    token = _service.login(email=body.email, password=body.password)
    return _json(TokenResponse(
        data=TokenData(
            access_token=token,
            expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
    ))
