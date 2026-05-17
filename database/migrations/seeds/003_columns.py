"""Seed : colonnes de démonstration."""
from database.repositories.board_repository import BoardRepository
from database.repositories.column_repository import ColumnRepository

_board_repo = BoardRepository()
_col_repo = ColumnRepository()

_COLUMNS = {
    "Projet Alpha": ["Backlog", "En cours", "Review", "Terminé"],
    "Projet Beta":  ["À faire", "En développement", "Livré"],
}


def run() -> None:
    for board_name, columns in _COLUMNS.items():
        rows = _board_repo.find_by({"name": board_name})
        if not rows:
            raise RuntimeError(f"Board '{board_name}' introuvable — lancez d'abord 002_boards")
        board_id = rows[0]["id"]

        if _col_repo.count_by_board(board_id) > 0:
            print(f"colonnes '{board_name}' déjà présentes, ignoré", end=" ")
            continue

        for pos, name in enumerate(columns):
            _col_repo.create(board_id=board_id, name=name, position=pos)
