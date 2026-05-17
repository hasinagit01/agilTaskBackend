import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers.auth_router import router as auth_router
from api.routers.board_router import router as board_router
from config import CORS_ORIGIN, HOST, LOG_FILE, LOG_LEVEL, PORT
from services.business_error import BusinessError

_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)-8s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)

_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(_formatter)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    handlers=[_stream_handler, _file_handler],
)

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _logger.info("Application démarrée — lancez 'python scripts/db.py migrate' pour initialiser la BDD")
    yield


_TAGS_METADATA = [
    {"name": "auth",      "description": "Inscription et connexion (JWT)"},
    {"name": "boards",    "description": "Création et gestion des boards"},
    {"name": "members",   "description": "Membres d'un board et leurs rôles (owner / member / viewer)"},
    {"name": "columns",   "description": "Colonnes d'un board (Todo, Doing, Done…)"},
    {"name": "cards",     "description": "Cartes dans une colonne, déplacement et réordonnancement"},
    {"name": "labels",    "description": "Labels de couleur créés au niveau board, attachés aux cartes"},
    {"name": "assignees", "description": "Affectation de membres à une carte"},
]

app = FastAPI(
    title="Mini Trello API",
    description=(
        "API REST de gestion de projet de type Trello.\n\n"
        "**Authentification** : obtenir un token via `POST /auth/login`, "
        "puis l'envoyer dans le header `Authorization: Bearer <token>`."
    ),
    version="2.0.0",
    openapi_tags=_TAGS_METADATA,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router)
app.include_router(board_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
