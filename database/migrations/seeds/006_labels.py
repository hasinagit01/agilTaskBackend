"""Seed : labels par board."""
from database.repositories.board_repository import BoardRepository
from database.repositories.label_repository import LabelRepository

_board_repo = BoardRepository()
_label_repo = LabelRepository()

_LABELS = {
    "Projet Alpha": [
        ("Bug",           "#ef4444"),
        ("Feature",       "#22c55e"),
        ("Urgent",        "#f97316"),
        ("Documentation", "#3b82f6"),
    ],
    "Projet Beta": [
        ("Backend",  "#8b5cf6"),
        ("Frontend", "#ec4899"),
    ],
}


def run() -> None:
    for board_name, labels in _LABELS.items():
        rows = _board_repo.find_by({"name": board_name})
        if not rows:
            raise RuntimeError(f"Board '{board_name}' introuvable — lancez d'abord 002_boards")
        board_id = rows[0]["id"]

        if _label_repo.find_by_board(board_id):
            print(f"labels '{board_name}' déjà présents, ignoré", end=" ")
            continue

        for name, color in labels:
            _label_repo.create(board_id=board_id, name=name, color=color)
