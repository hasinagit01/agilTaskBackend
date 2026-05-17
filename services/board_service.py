from typing import Dict, List, Optional

from database.repositories.board_member_repository import BoardMemberRepository
from database.repositories.board_repository import BoardRepository
from database.repositories.column_repository import ColumnRepository
from database.exceptions import DuplicateError
from models import Board, Column
from services.business_error import BusinessError
from utils import ModelMapper

_board_repo = BoardRepository()
_column_repo = ColumnRepository()
_member_repo = BoardMemberRepository()

# Hiérarchie des rôles : plus le chiffre est élevé, plus le rôle est puissant
_ROLE_LEVEL: Dict[str, int] = {"viewer": 1, "member": 2, "owner": 3}

ROLES = list(_ROLE_LEVEL.keys())


class BoardService:

    # ── Helpers permission ────────────────────────────────────────────────────

    def _require_role(self, board_id: int, user_id: int, min_role: str) -> str:
        """Vérifie que l'utilisateur a au moins `min_role` sur ce board. Retourne son rôle réel."""
        role = _member_repo.find_role(board_id, user_id)
        if role is None:
            raise BusinessError(f"Board {board_id} non trouvé", status_code=404)
        if _ROLE_LEVEL[role] < _ROLE_LEVEL[min_role]:
            raise BusinessError("Permission insuffisante", status_code=403)
        return role

    # ── Boards ────────────────────────────────────────────────────────────────

    def create_board(self, name: str, user_id: int) -> Board:
        name = name.strip()
        if len(name) < 2:
            raise BusinessError("Le nom du board doit contenir au moins 2 caractères")
        board_id = _board_repo.create(name=name, owner_id=user_id)
        _member_repo.add(board_id=board_id, user_id=user_id, role="owner")
        return ModelMapper.to_model(Board, _board_repo.find_by({"id": board_id})[0])

    def list_boards(self, user_id: int, page: int, limit: int) -> List[Board]:
        offset = (page - 1) * limit
        rows = _board_repo.find_by_member(user_id=user_id, limit=limit, offset=offset)
        return [ModelMapper.to_model(Board, row) for row in rows]

    def count_boards(self, user_id: int) -> int:
        return _board_repo.count_by_member(user_id)

    def get_board(self, board_id: int, user_id: int, min_role: str = "viewer") -> Board:
        self._require_role(board_id, user_id, min_role)
        rows = _board_repo.find_by({"id": board_id})
        if not rows:
            raise BusinessError(f"Board {board_id} non trouvé", status_code=404)
        return ModelMapper.to_model(Board, rows[0])

    def update_board(self, board_id: int, name: str, user_id: int) -> Board:
        self._require_role(board_id, user_id, "owner")
        name = name.strip()
        if len(name) < 2:
            raise BusinessError("Le nom du board doit contenir au moins 2 caractères")
        _board_repo.update(board_id, name)
        return ModelMapper.to_model(Board, _board_repo.find_by({"id": board_id})[0])

    def delete_board(self, board_id: int, user_id: int) -> None:
        self._require_role(board_id, user_id, "owner")
        _board_repo.delete_by_ids([board_id])

    # ── Membres ───────────────────────────────────────────────────────────────

    def list_members(self, board_id: int, user_id: int) -> List[Dict]:
        self._require_role(board_id, user_id, "viewer")
        return _member_repo.find_by_board(board_id)

    def add_member(self, board_id: int, new_user_id: int, role: str, requester_id: int) -> None:
        self._require_role(board_id, requester_id, "owner")
        if role not in ROLES:
            raise BusinessError(f"Rôle invalide. Valeurs acceptées : {ROLES}")
        if role == "owner":
            raise BusinessError("Impossible d'ajouter un autre owner. Utilisez 'member' ou 'viewer'.")
        existing = _member_repo.find_role(board_id, new_user_id)
        if existing is not None:
            raise BusinessError("Cet utilisateur est déjà membre du board", status_code=409)
        try:
            _member_repo.add(board_id=board_id, user_id=new_user_id, role=role)
        except DuplicateError:
            raise BusinessError("Cet utilisateur est déjà membre du board", status_code=409)

    def update_member_role(self, board_id: int, target_user_id: int, role: str, requester_id: int) -> None:
        self._require_role(board_id, requester_id, "owner")
        if role == "owner":
            raise BusinessError("Impossible de promouvoir un membre en owner.")
        if _member_repo.find_role(board_id, target_user_id) is None:
            raise BusinessError("Membre non trouvé", status_code=404)
        if target_user_id == requester_id:
            raise BusinessError("Vous ne pouvez pas modifier votre propre rôle")
        _member_repo.update_role(board_id, target_user_id, role)

    def remove_member(self, board_id: int, target_user_id: int, requester_id: int) -> None:
        self._require_role(board_id, requester_id, "owner")
        if target_user_id == requester_id:
            raise BusinessError("Le owner ne peut pas se retirer du board")
        if _member_repo.find_role(board_id, target_user_id) is None:
            raise BusinessError("Membre non trouvé", status_code=404)
        _member_repo.remove(board_id, target_user_id)

    # ── Colonnes ──────────────────────────────────────────────────────────────

    def create_column(self, board_id: int, name: str, user_id: int) -> Column:
        self._require_role(board_id, user_id, "member")
        name = name.strip()
        if len(name) < 2:
            raise BusinessError("Le nom de la colonne doit contenir au moins 2 caractères")
        position = _column_repo.count_by_board(board_id)
        col_id = _column_repo.create(board_id=board_id, name=name, position=position)
        return ModelMapper.to_model(Column, _column_repo.find_by({"id": col_id})[0])

    def list_columns(self, board_id: int, user_id: int) -> List[Column]:
        self._require_role(board_id, user_id, "viewer")
        rows = _column_repo.find_by_board(board_id)
        return [ModelMapper.to_model(Column, row) for row in rows]

    def get_column(self, board_id: int, column_id: int, user_id: int) -> Column:
        self._require_role(board_id, user_id, "viewer")
        rows = _column_repo.find_by({"id": column_id, "board_id": board_id})
        if not rows:
            raise BusinessError(f"Colonne {column_id} non trouvée", status_code=404)
        return ModelMapper.to_model(Column, rows[0])

    def update_column(self, board_id: int, column_id: int, name: str, position: Optional[int], user_id: int) -> Column:
        column = self.get_column(board_id, column_id, user_id)
        self._require_role(board_id, user_id, "member")
        name = name.strip()
        if len(name) < 2:
            raise BusinessError("Le nom de la colonne doit contenir au moins 2 caractères")
        new_position = position if position is not None else column.position
        _column_repo.update(column_id, name=name, position=new_position)
        return ModelMapper.to_model(Column, _column_repo.find_by({"id": column_id})[0])

    def delete_column(self, board_id: int, column_id: int, user_id: int) -> None:
        column = self.get_column(board_id, column_id, user_id)
        self._require_role(board_id, user_id, "member")
        _column_repo.delete_by_ids([column.id])

    def reorder_columns(self, board_id: int, ordered_ids: List[int], user_id: int) -> List[Column]:
        self._require_role(board_id, user_id, "member")
        existing = {row["id"] for row in _column_repo.find_by_board(board_id)}
        if set(ordered_ids) != existing:
            raise BusinessError("Les IDs ne correspondent pas aux colonnes de ce board")
        _column_repo.reorder(board_id, ordered_ids)
        return [ModelMapper.to_model(Column, row) for row in _column_repo.find_by_board(board_id)]
