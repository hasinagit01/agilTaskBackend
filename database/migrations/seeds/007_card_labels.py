"""Seed : attachement des labels aux cartes."""
from database.repositories.board_repository import BoardRepository
from database.repositories.card_repository import CardRepository
from database.repositories.column_repository import ColumnRepository
from database.repositories.label_repository import LabelRepository

_board_repo = BoardRepository()
_col_repo = ColumnRepository()
_card_repo = CardRepository()
_label_repo = LabelRepository()


def _get_label_id(board_id: int, name: str) -> int:
    for lb in _label_repo.find_by_board(board_id):
        if lb["name"] == name:
            return lb["id"]
    raise RuntimeError(f"Label '{name}' introuvable — lancez d'abord 006_labels")


def _get_card_id(board_id: int, col_name: str, card_title: str) -> int:
    for col in _col_repo.find_by_board(board_id):
        if col["name"] == col_name:
            for card in _card_repo.find_by_column(col["id"]):
                if card["title"] == card_title:
                    return card["id"]
    raise RuntimeError(f"Carte '{card_title}' introuvable dans '{col_name}'")


def run() -> None:
    alpha_rows = _board_repo.find_by({"name": "Projet Alpha"})
    if not alpha_rows:
        raise RuntimeError("Lancez d'abord le seed 002_boards")
    alpha_id = alpha_rows[0]["id"]

    attachments = [
        ("En cours", "API authentification",     "Bug"),
        ("En cours", "API authentification",     "Urgent"),
        ("En cours", "Tests unitaires service",  "Feature"),
        ("Review",   "Module boards et colonnes","Feature"),
        ("Review",   "Module boards et colonnes","Documentation"),
        ("Backlog",  "Architecture de la BDD",   "Documentation"),
    ]

    for col_name, card_title, label_name in attachments:
        try:
            card_id  = _get_card_id(alpha_id, col_name, card_title)
            label_id = _get_label_id(alpha_id, label_name)
        except RuntimeError:
            continue
        existing = _label_repo.find_by_card(card_id)
        if any(lb["id"] == label_id for lb in existing):
            continue
        _label_repo.attach_to_card(card_id, label_id)
