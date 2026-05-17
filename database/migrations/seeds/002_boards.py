"""Seed : boards de démonstration."""
from database.repositories.board_repository import BoardRepository
from database.repositories.user_repository import UserRepository

_board_repo = BoardRepository()
_user_repo = UserRepository()


def run() -> None:
    admin = _user_repo.find_by_email("admin@minitrello.dev")
    alice = _user_repo.find_by_email("alice@minitrello.dev")
    if not admin or not alice:
        raise RuntimeError("Lancez d'abord le seed 001_users")

    if _board_repo.find_by({"name": "Projet Alpha"}):
        print("déjà présents, ignoré", end=" ")
        return

    _board_repo.create(name="Projet Alpha", owner_id=admin["id"])
    _board_repo.create(name="Projet Beta",  owner_id=alice["id"])
