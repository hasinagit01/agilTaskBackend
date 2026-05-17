"""Seed : affectation des membres aux cartes."""
from database.repositories.board_repository import BoardRepository
from database.repositories.card_assignee_repository import CardAssigneeRepository
from database.repositories.card_repository import CardRepository
from database.repositories.column_repository import ColumnRepository
from database.repositories.user_repository import UserRepository

_board_repo = BoardRepository()
_col_repo = ColumnRepository()
_card_repo = CardRepository()
_user_repo = UserRepository()
_assignee_repo = CardAssigneeRepository()


def _get_card_id(board_id: int, col_name: str, card_title: str) -> int:
    for col in _col_repo.find_by_board(board_id):
        if col["name"] == col_name:
            for card in _card_repo.find_by_column(col["id"]):
                if card["title"] == card_title:
                    return card["id"]
    raise RuntimeError(f"Carte '{card_title}' introuvable dans '{col_name}'")


def run() -> None:
    admin = _user_repo.find_by_email("admin@minitrello.dev")
    alice = _user_repo.find_by_email("alice@minitrello.dev")
    if not admin or not alice:
        raise RuntimeError("Lancez d'abord le seed 001_users")

    alpha_rows = _board_repo.find_by({"name": "Projet Alpha"})
    beta_rows  = _board_repo.find_by({"name": "Projet Beta"})
    if not alpha_rows or not beta_rows:
        raise RuntimeError("Lancez d'abord le seed 002_boards")

    alpha_id = alpha_rows[0]["id"]
    beta_id  = beta_rows[0]["id"]

    # board_id, col_name, card_title, user_email
    assignments = [
        (alpha_id, "En cours", "API authentification",    "admin@minitrello.dev"),
        (alpha_id, "En cours", "Tests unitaires service", "alice@minitrello.dev"),
        (alpha_id, "Review",   "Module boards et colonnes","admin@minitrello.dev"),
        (beta_id,  "En développement", "Dashboard analytics", "alice@minitrello.dev"),
    ]

    for board_id, col_name, card_title, email in assignments:
        user = _user_repo.find_by_email(email)
        if not user:
            continue
        try:
            card_id = _get_card_id(board_id, col_name, card_title)
        except RuntimeError:
            continue
        existing = _assignee_repo.find_by_card(card_id)
        if any(a["user_id"] == user["id"] for a in existing):
            continue
        _assignee_repo.add(card_id, user["id"])
