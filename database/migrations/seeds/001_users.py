"""Seed : utilisateurs de démonstration."""
import bcrypt

from database.repositories.user_repository import UserRepository

_repo = UserRepository()

_USERS = [
    {"email": "admin@minitrello.dev", "password": "Admin1234!"},
    {"email": "alice@minitrello.dev",  "password": "Alice1234!"},
    {"email": "bob@minitrello.dev",    "password": "Bob12345!"},
]


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def run() -> None:
    if _repo.find_by_email(_USERS[0]["email"]):
        print("déjà présents, ignoré", end=" ")
        return
    for u in _USERS:
        _repo.create(email=u["email"], password_hash=_hash(u["password"]))
