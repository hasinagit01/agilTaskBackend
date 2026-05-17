"""Seed : membres des boards."""
from database.repositories.board_member_repository import BoardMemberRepository
from database.repositories.board_repository import BoardRepository
from database.repositories.user_repository import UserRepository

_board_repo = BoardRepository()
_user_repo = UserRepository()
_member_repo = BoardMemberRepository()


def run() -> None:
    admin = _user_repo.find_by_email("admin@minitrello.dev")
    alice = _user_repo.find_by_email("alice@minitrello.dev")
    bob   = _user_repo.find_by_email("bob@minitrello.dev")
    if not all([admin, alice, bob]):
        raise RuntimeError("Lancez d'abord le seed 001_users")

    alpha_rows = _board_repo.find_by({"name": "Projet Alpha"})
    beta_rows  = _board_repo.find_by({"name": "Projet Beta"})
    if not alpha_rows or not beta_rows:
        raise RuntimeError("Lancez d'abord le seed 002_boards")

    alpha_id = alpha_rows[0]["id"]
    beta_id  = beta_rows[0]["id"]

    # Membres Projet Alpha : admin=owner (déjà ajouté à la création), alice=member, bob=viewer
    if _member_repo.find_role(alpha_id, admin["id"]) is None:
        _member_repo.add(board_id=alpha_id, user_id=admin["id"], role="owner")
    if _member_repo.find_role(alpha_id, alice["id"]) is None:
        _member_repo.add(board_id=alpha_id, user_id=alice["id"], role="member")
    if _member_repo.find_role(alpha_id, bob["id"]) is None:
        _member_repo.add(board_id=alpha_id, user_id=bob["id"],   role="viewer")

    # Membres Projet Beta : alice=owner (déjà ajouté), admin=member
    if _member_repo.find_role(beta_id, alice["id"]) is None:
        _member_repo.add(board_id=beta_id, user_id=alice["id"], role="owner")
    if _member_repo.find_role(beta_id, admin["id"]) is None:
        _member_repo.add(board_id=beta_id, user_id=admin["id"], role="member")
