from database.exceptions import DuplicateError
from database.repositories.board_member_repository import BoardMemberRepository
from database.repositories.card_assignee_repository import CardAssigneeRepository
from database.repositories.card_repository import CardRepository
from services.board_service import BoardService
from services.business_error import BusinessError

_assignee_repo = CardAssigneeRepository()
_card_repo = CardRepository()
_member_repo = BoardMemberRepository()
_board_service = BoardService()


class AssigneeService:

    def add_assignee(self, board_id: int, card_id: int, target_user_id: int, user_id: int) -> None:
        _board_service.get_board(board_id, user_id, min_role="member")
        if _member_repo.find_role(board_id, target_user_id) is None:
            raise BusinessError("Cet utilisateur n'est pas membre du board", status_code=404)
        if not _card_repo.find_by({"id": card_id}):
            raise BusinessError(f"Carte {card_id} non trouvée", status_code=404)
        try:
            _assignee_repo.add(card_id, target_user_id)
        except DuplicateError:
            raise BusinessError("Cet utilisateur est déjà assigné à cette carte", status_code=409)

    def remove_assignee(self, board_id: int, card_id: int, target_user_id: int, user_id: int) -> None:
        _board_service.get_board(board_id, user_id, min_role="member")
        if _assignee_repo.remove(card_id, target_user_id) == 0:
            raise BusinessError("Cet utilisateur n'est pas assigné à cette carte", status_code=404)
