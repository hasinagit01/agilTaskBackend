from datetime import date
from typing import List, Optional

from database.repositories.card_repository import CardRepository
from database.repositories.column_repository import ColumnRepository
from models import Card
from services.board_service import BoardService
from services.business_error import BusinessError
from utils import ModelMapper

_card_repo = CardRepository()
_column_repo = ColumnRepository()
_board_service = BoardService()


class CardService:
    def _get_column_or_404(self, board_id: int, column_id: int, user_id: int, min_role: str = "viewer"):
        """Vérifie l'accès au board et que la colonne appartient au board."""
        _board_service.get_board(board_id, user_id, min_role=min_role)
        rows = _column_repo.find_by({"id": column_id, "board_id": board_id})
        if not rows:
            raise BusinessError(f"Colonne {column_id} non trouvée dans ce board", status_code=404)
        return rows[0]

    def create_card(self, board_id: int, column_id: int, title: str, description: Optional[str], due_date: Optional[date], user_id: int) -> Card:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        title = title.strip()
        if len(title) < 2:
            raise BusinessError("Le titre doit contenir au moins 2 caractères")
        position = _card_repo.count_by_column(column_id)
        card_id = _card_repo.create(
            column_id=column_id,
            title=title,
            description=(description or "").strip(),
            position=position,
            due_date=due_date.isoformat() if due_date else None,
        )
        return ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])

    def list_cards(self, board_id: int, column_id: int, user_id: int) -> List[Card]:
        self._get_column_or_404(board_id, column_id, user_id)
        rows = _card_repo.find_by_column(column_id)
        return [ModelMapper.to_model(Card, row) for row in rows]

    def get_card(self, board_id: int, column_id: int, card_id: int, user_id: int) -> Card:
        self._get_column_or_404(board_id, column_id, user_id)
        rows = _card_repo.find_by({"id": card_id, "column_id": column_id})
        if not rows:
            raise BusinessError(f"Carte {card_id} non trouvée", status_code=404)
        return ModelMapper.to_model(Card, rows[0])

    def update_card(self, board_id: int, column_id: int, card_id: int, title: str, description: Optional[str], position: Optional[int], due_date: Optional[date], user_id: int) -> Card:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        card = self.get_card(board_id, column_id, card_id, user_id)
        title = title.strip()
        if len(title) < 2:
            raise BusinessError("Le titre doit contenir au moins 2 caractères")
        _card_repo.update(
            card_id=card_id,
            title=title,
            description=(description or "").strip(),
            position=position if position is not None else card.position,
            due_date=due_date.isoformat() if due_date else None,
        )
        return ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])

    def move_card(self, board_id: int, column_id: int, card_id: int, target_column_id: int, position: Optional[int], user_id: int) -> Card:
        card = self.get_card(board_id, column_id, card_id, user_id)
        self._get_column_or_404(board_id, target_column_id, user_id, min_role="member")

        if target_column_id == column_id:
            count = _card_repo.count_by_column(column_id)
            new_pos = position if position is not None else count - 1
            new_pos = max(0, min(new_pos, count - 1))
            old_pos = card.position
            if new_pos == old_pos:
                return ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])
            if new_pos > old_pos:
                _card_repo.shift_range(column_id, old_pos + 1, new_pos, -1)
            else:
                _card_repo.shift_range(column_id, new_pos, old_pos - 1, +1)
        else:
            count_target = _card_repo.count_by_column(target_column_id)
            new_pos = position if position is not None else count_target
            new_pos = max(0, min(new_pos, count_target))
            _card_repo.shift_down(column_id, card.position)
            _card_repo.shift_up(target_column_id, new_pos)

        _card_repo.move(card_id=card_id, target_column_id=target_column_id, position=new_pos)
        return ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])

    def reorder_cards(self, board_id: int, column_id: int, ordered_ids: List[int], user_id: int) -> List[Card]:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        existing = {row["id"] for row in _card_repo.find_by_column(column_id)}
        if set(ordered_ids) != existing:
            raise BusinessError("Les IDs ne correspondent pas aux cartes de cette colonne")
        _card_repo.reorder(column_id, ordered_ids)
        return [ModelMapper.to_model(Card, row) for row in _card_repo.find_by_column(column_id)]

    def delete_card(self, board_id: int, column_id: int, card_id: int, user_id: int) -> None:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        card = self.get_card(board_id, column_id, card_id, user_id)
        _card_repo.delete_by_ids([card.id])
