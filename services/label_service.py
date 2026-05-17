from typing import List

from database.exceptions import DuplicateError
from database.repositories.card_repository import CardRepository
from database.repositories.label_repository import LabelRepository
from models import Label
from services.board_service import BoardService
from services.business_error import BusinessError
from utils import ModelMapper

_label_repo = LabelRepository()
_card_repo = CardRepository()
_board_service = BoardService()


class LabelService:

    def _get_label_or_404(self, label_id: int, board_id: int) -> Label:
        rows = _label_repo.find_by({"id": label_id, "board_id": board_id})
        if not rows:
            raise BusinessError(f"Label {label_id} non trouvé", status_code=404)
        return ModelMapper.to_model(Label, rows[0])

    def create_label(self, board_id: int, name: str, color: str, user_id: int) -> Label:
        _board_service.get_board(board_id, user_id, min_role="member")
        name = name.strip()
        if not name:
            raise BusinessError("Le nom du label ne peut pas être vide")
        label_id = _label_repo.create(board_id=board_id, name=name, color=color)
        return ModelMapper.to_model(Label, _label_repo.find_by({"id": label_id})[0])

    def list_labels(self, board_id: int, user_id: int) -> List[Label]:
        _board_service.get_board(board_id, user_id, min_role="viewer")
        rows = _label_repo.find_by_board(board_id)
        return [ModelMapper.to_model(Label, row) for row in rows]

    def update_label(self, board_id: int, label_id: int, name: str, color: str, user_id: int) -> Label:
        _board_service.get_board(board_id, user_id, min_role="member")
        self._get_label_or_404(label_id, board_id)
        name = name.strip()
        if not name:
            raise BusinessError("Le nom du label ne peut pas être vide")
        _label_repo.update(label_id, name=name, color=color)
        return ModelMapper.to_model(Label, _label_repo.find_by({"id": label_id})[0])

    def delete_label(self, board_id: int, label_id: int, user_id: int) -> None:
        _board_service.get_board(board_id, user_id, min_role="member")
        self._get_label_or_404(label_id, board_id)
        _label_repo.delete_by_ids([label_id])

    def attach_to_card(self, board_id: int, card_id: int, label_id: int, user_id: int) -> None:
        _board_service.get_board(board_id, user_id, min_role="member")
        self._get_label_or_404(label_id, board_id)
        if not _card_repo.find_by({"id": card_id}):
            raise BusinessError(f"Carte {card_id} non trouvée", status_code=404)
        try:
            _label_repo.attach_to_card(card_id, label_id)
        except DuplicateError:
            raise BusinessError("Ce label est déjà attaché à cette carte", status_code=409)

    def detach_from_card(self, board_id: int, card_id: int, label_id: int, user_id: int) -> None:
        _board_service.get_board(board_id, user_id, min_role="member")
        self._get_label_or_404(label_id, board_id)
        if _label_repo.detach_from_card(card_id, label_id) == 0:
            raise BusinessError("Ce label n'est pas attaché à cette carte", status_code=404)
