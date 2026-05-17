"""Seed : cartes de démonstration."""
from database.repositories.board_repository import BoardRepository
from database.repositories.card_repository import CardRepository
from database.repositories.column_repository import ColumnRepository

_board_repo = BoardRepository()
_col_repo = ColumnRepository()
_card_repo = CardRepository()

# board_name → { col_name → [(title, description, due_date)] }
_CARDS = {
    "Projet Alpha": {
        "Backlog": [
            ("Analyse des besoins",    "Recueil et formalisation des exigences fonctionnelles", None),
            ("Rédaction des specs",    "Document de spécifications techniques v1",              None),
            ("Architecture de la BDD", "Schéma entité-relation et choix du moteur",             None),
        ],
        "En cours": [
            ("API authentification",        "JWT + bcrypt, endpoints register/login",  "2026-06-15"),
            ("Tests unitaires service",     "Couverture des services métier à 80 %",   "2026-06-20"),
        ],
        "Review": [
            ("Module boards et colonnes", "CRUD complet avec gestion des rôles", "2026-06-10"),
        ],
        "Terminé": [
            ("Setup du projet",   "Arborescence, venv, requirements.txt", None),
            ("Pipeline CI/CD",    "GitHub Actions : lint + tests",        None),
        ],
    },
    "Projet Beta": {
        "À faire": [
            ("Roadmap Q3",            "Priorisation des features pour le trimestre", None),
            ("Interviews utilisateurs", "Sessions avec 5 utilisateurs cibles",        None),
        ],
        "En développement": [
            ("Dashboard analytics", "Graphiques temps réel avec Chart.js", "2026-07-01"),
        ],
        "Livré": [
            ("Onboarding flow", "Parcours d'inscription en 3 étapes", None),
        ],
    },
}


def run() -> None:
    for board_name, columns in _CARDS.items():
        rows = _board_repo.find_by({"name": board_name})
        if not rows:
            raise RuntimeError(f"Board '{board_name}' introuvable — lancez d'abord 002_boards")
        board_id = rows[0]["id"]

        for col_name, cards in columns.items():
            col_rows = [c for c in _col_repo.find_by_board(board_id) if c["name"] == col_name]
            if not col_rows:
                raise RuntimeError(f"Colonne '{col_name}' introuvable — lancez d'abord 003_columns")
            col_id = col_rows[0]["id"]

            if _card_repo.count_by_column(col_id) > 0:
                continue

            for pos, (title, description, due_date) in enumerate(cards):
                _card_repo.create(
                    column_id=col_id,
                    title=title,
                    description=description,
                    position=pos,
                    due_date=due_date,
                )
