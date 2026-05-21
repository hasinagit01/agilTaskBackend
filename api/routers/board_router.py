from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user
from models import Card, User
from schemas.activity_schema import ActivityListResponse, ActivityLogResponse, ActorResponse
from schemas.board_schema import (
    BoardListResponse,
    BoardResponse,
    CreateBoardRequest,
    SingleBoardResponse,
    UpdateBoardRequest,
)
from schemas.board_member_schema import (
    AddMemberRequest,
    MemberListResponse,
    MemberResponse,
    UpdateMemberRoleRequest,
)
from schemas.card_schema import (
    CardListResponse,
    CardResponse,
    CreateCardRequest,
    MoveCardRequest,
    ReorderCardsRequest,
    SingleCardResponse,
    UpdateCardRequest,
)
from schemas.column_schema import (
    ColumnListResponse,
    ColumnResponse,
    CreateColumnRequest,
    ReorderColumnsRequest,
    SingleColumnResponse,
    UpdateColumnRequest,
)
from schemas.label_schema import (
    CreateLabelRequest,
    LabelListResponse,
    LabelResponse,
    SingleLabelResponse,
    UpdateLabelRequest,
)
from services.activity_service import ActivityService
from services.assignee_service import AssigneeService
from services.board_service import BoardService
from services.card_service import CardService
from services.label_service import LabelService
from websocket.manager import manager

router = APIRouter(prefix="/boards", tags=["boards"])

_service = BoardService()
_card_service = CardService()
_label_service = LabelService()
_assignee_service = AssigneeService()
_activity_service = ActivityService()


def _json(model, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=model.model_dump(mode="json"), status_code=status_code)


def _card_json(card: Card, status_code: int = 200) -> JSONResponse:
    return _json(SingleCardResponse(data=CardResponse.model_validate(_card_service.enrich(card))), status_code)


def _cards_json(cards) -> JSONResponse:
    data = [CardResponse.model_validate(_card_service.enrich(c)) for c in cards]
    return _json(CardListResponse(data=data))


def _column_json(column, status_code: int = 200) -> JSONResponse:
    return _json(SingleColumnResponse(data=ColumnResponse.model_validate(column)), status_code)


def _columns_json(columns) -> JSONResponse:
    data = [ColumnResponse.model_validate(c) for c in columns]
    return _json(ColumnListResponse(data=data))


def _card_data(card: Card) -> dict:
    return CardResponse.model_validate(_card_service.enrich(card)).model_dump(mode="json")


def _column_data(column) -> dict:
    return ColumnResponse.model_validate(column).model_dump(mode="json")


async def _broadcast(board_id: int, event_type: str, data: dict, actor_id: int) -> None:
    """Diffuse un événement à tous les clients WS du board. Silencieux en cas d'erreur."""
    try:
        await manager.broadcast(board_id, {"type": event_type, "actor_id": actor_id, "data": data})
    except Exception:
        pass


# ── Boards ────────────────────────────────────────────────────────────────────

@router.get("/", tags=["boards"], summary="Lister mes boards", response_model=BoardListResponse)
def list_boards(
    page:  Annotated[int, Query(ge=1)]        = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    current_user: User = Depends(get_current_user),
):
    boards = _service.list_boards(user_id=current_user.id, page=page, limit=limit)
    total  = _service.count_boards(user_id=current_user.id)
    return _json(BoardListResponse(
        data=[BoardResponse.model_validate(b) for b in boards],
        total=total,
        page=page,
        limit=limit,
    ))


@router.post("/", tags=["boards"], summary="Créer un board", response_model=SingleBoardResponse, status_code=201)
def create_board(body: CreateBoardRequest, current_user: User = Depends(get_current_user)):
    board = _service.create_board(name=body.name, user_id=current_user.id)
    return _json(SingleBoardResponse(data=BoardResponse.model_validate(board)), status_code=201)


@router.get("/{board_id}", tags=["boards"], summary="Obtenir un board", response_model=SingleBoardResponse)
def get_board(board_id: int, current_user: User = Depends(get_current_user)):
    board = _service.get_board(board_id=board_id, user_id=current_user.id)
    return _json(SingleBoardResponse(data=BoardResponse.model_validate(board)))


@router.put("/{board_id}", tags=["boards"], summary="Renommer un board", response_model=SingleBoardResponse)
async def update_board(board_id: int, body: UpdateBoardRequest, current_user: User = Depends(get_current_user)):
    board = _service.update_board(board_id=board_id, name=body.name, user_id=current_user.id)
    response = _json(SingleBoardResponse(data=BoardResponse.model_validate(board)))
    await _broadcast(board_id, "board.renamed", {"board_id": board_id, "name": board.name}, current_user.id)
    return response


@router.delete("/{board_id}", tags=["boards"], summary="Supprimer un board", status_code=204)
def delete_board(board_id: int, current_user: User = Depends(get_current_user)):
    _service.delete_board(board_id=board_id, user_id=current_user.id)


# ── Members ───────────────────────────────────────────────────────────────────

@router.get("/{board_id}/members/", tags=["members"], summary="Lister les membres", response_model=MemberListResponse)
def list_members(board_id: int, current_user: User = Depends(get_current_user)):
    members = _service.list_members(board_id=board_id, user_id=current_user.id)
    return _json(MemberListResponse(data=[MemberResponse(**m) for m in members]))


@router.post("/{board_id}/members/", tags=["members"], summary="Ajouter un membre", status_code=204)
async def add_member(board_id: int, body: AddMemberRequest, current_user: User = Depends(get_current_user)):
    _service.add_member(board_id=board_id, new_user_id=body.user_id, role=body.role, requester_id=current_user.id)
    await _broadcast(board_id, "member.added", {"user_id": body.user_id, "role": body.role}, current_user.id)


@router.put("/{board_id}/members/{user_id}", tags=["members"], summary="Modifier le rôle d'un membre", status_code=204)
async def update_member_role(board_id: int, user_id: int, body: UpdateMemberRoleRequest, current_user: User = Depends(get_current_user)):
    _service.update_member_role(board_id=board_id, target_user_id=user_id, role=body.role, requester_id=current_user.id)
    await _broadcast(board_id, "member.updated", {"user_id": user_id, "role": body.role}, current_user.id)


@router.delete("/{board_id}/members/{user_id}", tags=["members"], summary="Retirer un membre", status_code=204)
async def remove_member(board_id: int, user_id: int, current_user: User = Depends(get_current_user)):
    _service.remove_member(board_id=board_id, target_user_id=user_id, requester_id=current_user.id)
    await _broadcast(board_id, "member.removed", {"user_id": user_id}, current_user.id)


# ── Columns ───────────────────────────────────────────────────────────────────

@router.get("/{board_id}/columns/", tags=["columns"], summary="Lister les colonnes", response_model=ColumnListResponse)
def list_columns(board_id: int, current_user: User = Depends(get_current_user)):
    columns = _service.list_columns(board_id=board_id, user_id=current_user.id)
    return _json(ColumnListResponse(data=[ColumnResponse.model_validate(c) for c in columns]))


@router.post("/{board_id}/columns/", tags=["columns"], summary="Créer une colonne", response_model=SingleColumnResponse, status_code=201)
async def create_column(board_id: int, body: CreateColumnRequest, current_user: User = Depends(get_current_user)):
    column = _service.create_column(board_id=board_id, name=body.name, user_id=current_user.id)
    response = _json(SingleColumnResponse(data=ColumnResponse.model_validate(column)), status_code=201)
    await _broadcast(board_id, "column.created", _column_data(column), current_user.id)
    return response


@router.get("/{board_id}/columns/{column_id}", tags=["columns"], summary="Obtenir une colonne", response_model=SingleColumnResponse)
def get_column(board_id: int, column_id: int, current_user: User = Depends(get_current_user)):
    column = _service.get_column(board_id=board_id, column_id=column_id, user_id=current_user.id)
    return _json(SingleColumnResponse(data=ColumnResponse.model_validate(column)))


@router.put("/{board_id}/columns/{column_id}", tags=["columns"], summary="Modifier une colonne", response_model=SingleColumnResponse)
async def update_column(board_id: int, column_id: int, body: UpdateColumnRequest, current_user: User = Depends(get_current_user)):
    column = _service.update_column(
        board_id=board_id, column_id=column_id,
        name=body.name, position=body.position, user_id=current_user.id,
    )
    response = _json(SingleColumnResponse(data=ColumnResponse.model_validate(column)))
    await _broadcast(board_id, "column.updated", _column_data(column), current_user.id)
    return response


@router.delete("/{board_id}/columns/{column_id}", tags=["columns"], summary="Supprimer une colonne", status_code=204)
async def delete_column(board_id: int, column_id: int, current_user: User = Depends(get_current_user)):
    _service.delete_column(board_id=board_id, column_id=column_id, user_id=current_user.id)
    await _broadcast(board_id, "column.deleted", {"column_id": column_id}, current_user.id)


@router.patch("/{board_id}/columns/reorder", tags=["columns"], summary="Réordonner les colonnes", response_model=ColumnListResponse)
async def reorder_columns(board_id: int, body: ReorderColumnsRequest, current_user: User = Depends(get_current_user)):
    columns = _service.reorder_columns(board_id=board_id, ordered_ids=body.ordered_ids, user_id=current_user.id)
    response = _json(ColumnListResponse(data=[ColumnResponse.model_validate(c) for c in columns]))
    await _broadcast(board_id, "column.reordered", {"columns": [_column_data(c) for c in columns]}, current_user.id)
    return response


# ── Cards ─────────────────────────────────────────────────────────────────────

@router.get("/{board_id}/columns/{column_id}/cards/", tags=["cards"], summary="Lister les cartes", response_model=CardListResponse)
def list_cards(board_id: int, column_id: int, current_user: User = Depends(get_current_user)):
    cards = _card_service.list_cards(board_id=board_id, column_id=column_id, user_id=current_user.id)
    return _cards_json(cards)


@router.post("/{board_id}/columns/{column_id}/cards/", tags=["cards"], summary="Créer une carte", response_model=SingleCardResponse, status_code=201)
async def create_card(board_id: int, column_id: int, body: CreateCardRequest, current_user: User = Depends(get_current_user)):
    card = _card_service.create_card(
        board_id=board_id, column_id=column_id,
        title=body.title, description=body.description,
        due_date=body.due_date, user_id=current_user.id,
    )
    data = _card_data(card)
    response = _json(SingleCardResponse(data=CardResponse.model_validate(data)), status_code=201)
    await _broadcast(board_id, "card.created", data, current_user.id)
    return response


@router.get("/{board_id}/columns/{column_id}/cards/{card_id}", tags=["cards"], summary="Obtenir une carte", response_model=SingleCardResponse)
def get_card(board_id: int, column_id: int, card_id: int, current_user: User = Depends(get_current_user)):
    card = _card_service.get_card(board_id=board_id, column_id=column_id, card_id=card_id, user_id=current_user.id)
    return _card_json(card)


@router.put("/{board_id}/columns/{column_id}/cards/{card_id}", tags=["cards"], summary="Modifier une carte", response_model=SingleCardResponse)
async def update_card(board_id: int, column_id: int, card_id: int, body: UpdateCardRequest, current_user: User = Depends(get_current_user)):
    card = _card_service.update_card(
        board_id=board_id, column_id=column_id, card_id=card_id,
        title=body.title, description=body.description,
        position=body.position, due_date=body.due_date,
        user_id=current_user.id,
    )
    data = _card_data(card)
    response = _json(SingleCardResponse(data=CardResponse.model_validate(data)))
    await _broadcast(board_id, "card.updated", data, current_user.id)
    return response


@router.patch("/{board_id}/columns/{column_id}/cards/{card_id}/move", tags=["cards"], summary="Déplacer une carte vers une autre colonne", response_model=SingleCardResponse)
async def move_card(board_id: int, column_id: int, card_id: int, body: MoveCardRequest, current_user: User = Depends(get_current_user)):
    card = _card_service.move_card(
        board_id=board_id, column_id=column_id, card_id=card_id,
        target_column_id=body.target_column_id,
        position=body.position, user_id=current_user.id,
    )
    data = _card_data(card)
    response = _json(SingleCardResponse(data=CardResponse.model_validate(data)))
    await _broadcast(board_id, "card.moved", {**data, "from_column_id": column_id}, current_user.id)
    return response


@router.delete("/{board_id}/columns/{column_id}/cards/{card_id}", tags=["cards"], summary="Supprimer une carte", status_code=204)
async def delete_card(board_id: int, column_id: int, card_id: int, current_user: User = Depends(get_current_user)):
    _card_service.delete_card(board_id=board_id, column_id=column_id, card_id=card_id, user_id=current_user.id)
    await _broadcast(board_id, "card.deleted", {"card_id": card_id, "column_id": column_id}, current_user.id)


@router.patch("/{board_id}/columns/{column_id}/cards/reorder", tags=["cards"], summary="Réordonner les cartes d'une colonne", response_model=CardListResponse)
async def reorder_cards(board_id: int, column_id: int, body: ReorderCardsRequest, current_user: User = Depends(get_current_user)):
    cards = _card_service.reorder_cards(board_id=board_id, column_id=column_id, ordered_ids=body.ordered_ids, user_id=current_user.id)
    data = [_card_data(c) for c in cards]
    response = _json(CardListResponse(data=[CardResponse.model_validate(d) for d in data]))
    await _broadcast(board_id, "card.reordered", {"column_id": column_id, "cards": data}, current_user.id)
    return response


# ── Labels ────────────────────────────────────────────────────────────────────

@router.get("/{board_id}/labels/", tags=["labels"], summary="Lister les labels du board", response_model=LabelListResponse)
def list_labels(board_id: int, current_user: User = Depends(get_current_user)):
    labels = _label_service.list_labels(board_id=board_id, user_id=current_user.id)
    return _json(LabelListResponse(data=[LabelResponse.model_validate(lb) for lb in labels]))


@router.post("/{board_id}/labels/", tags=["labels"], summary="Créer un label", response_model=SingleLabelResponse, status_code=201)
def create_label(board_id: int, body: CreateLabelRequest, current_user: User = Depends(get_current_user)):
    label = _label_service.create_label(board_id=board_id, name=body.name, color=body.color, user_id=current_user.id)
    return _json(SingleLabelResponse(data=LabelResponse.model_validate(label)), status_code=201)


@router.put("/{board_id}/labels/{label_id}", tags=["labels"], summary="Modifier un label", response_model=SingleLabelResponse)
def update_label(board_id: int, label_id: int, body: UpdateLabelRequest, current_user: User = Depends(get_current_user)):
    label = _label_service.update_label(board_id=board_id, label_id=label_id, name=body.name, color=body.color, user_id=current_user.id)
    return _json(SingleLabelResponse(data=LabelResponse.model_validate(label)))


@router.delete("/{board_id}/labels/{label_id}", tags=["labels"], summary="Supprimer un label", status_code=204)
def delete_label(board_id: int, label_id: int, current_user: User = Depends(get_current_user)):
    _label_service.delete_label(board_id=board_id, label_id=label_id, user_id=current_user.id)


@router.post("/{board_id}/columns/{column_id}/cards/{card_id}/labels/{label_id}", tags=["labels"], summary="Attacher un label à une carte", status_code=204)
async def attach_label(board_id: int, column_id: int, card_id: int, label_id: int, current_user: User = Depends(get_current_user)):
    _label_service.attach_to_card(board_id=board_id, card_id=card_id, label_id=label_id, user_id=current_user.id)
    await _broadcast(board_id, "label.attached", {"card_id": card_id, "label_id": label_id, "column_id": column_id}, current_user.id)


@router.delete("/{board_id}/columns/{column_id}/cards/{card_id}/labels/{label_id}", tags=["labels"], summary="Détacher un label d'une carte", status_code=204)
async def detach_label(board_id: int, column_id: int, card_id: int, label_id: int, current_user: User = Depends(get_current_user)):
    _label_service.detach_from_card(board_id=board_id, card_id=card_id, label_id=label_id, user_id=current_user.id)
    await _broadcast(board_id, "label.detached", {"card_id": card_id, "label_id": label_id, "column_id": column_id}, current_user.id)


# ── Assignees ─────────────────────────────────────────────────────────────────

@router.post("/{board_id}/columns/{column_id}/cards/{card_id}/assignees/{user_id}", tags=["assignees"], summary="Assigner un membre à une carte", status_code=204)
async def add_assignee(board_id: int, column_id: int, card_id: int, user_id: int, current_user: User = Depends(get_current_user)):
    _assignee_service.add_assignee(board_id=board_id, card_id=card_id, target_user_id=user_id, user_id=current_user.id)
    await _broadcast(board_id, "assignee.added", {"card_id": card_id, "user_id": user_id, "column_id": column_id}, current_user.id)


@router.delete("/{board_id}/columns/{column_id}/cards/{card_id}/assignees/{user_id}", tags=["assignees"], summary="Retirer un assignee d'une carte", status_code=204)
async def remove_assignee(board_id: int, column_id: int, card_id: int, user_id: int, current_user: User = Depends(get_current_user)):
    _assignee_service.remove_assignee(board_id=board_id, card_id=card_id, target_user_id=user_id, user_id=current_user.id)
    await _broadcast(board_id, "assignee.removed", {"card_id": card_id, "user_id": user_id, "column_id": column_id}, current_user.id)


# ===== ARCHIVES CARTES =====

@router.patch("/{board_id}/columns/{column_id}/cards/{card_id}/archive", tags=["cards"], summary="Archiver une carte", response_model=SingleCardResponse)
async def archive_card(board_id: int, column_id: int, card_id: int, current_user: User = Depends(get_current_user)):
    card = _card_service.archive_card(board_id=board_id, column_id=column_id, card_id=card_id, user_id=current_user.id)
    response = _card_json(card)
    await _broadcast(board_id, "card.archived", {"card_id": card_id, "column_id": column_id}, current_user.id)
    return response


@router.patch("/{board_id}/cards/{card_id}/unarchive", tags=["cards"], summary="Restaurer une carte archivée", response_model=SingleCardResponse)
async def unarchive_card(board_id: int, card_id: int, current_user: User = Depends(get_current_user)):
    card = _card_service.unarchive_card(board_id=board_id, card_id=card_id, user_id=current_user.id)
    data = _card_data(card)
    response = _json(SingleCardResponse(data=CardResponse.model_validate(data)))
    await _broadcast(board_id, "card.restored", data, current_user.id)
    return response


@router.get("/{board_id}/archives/cards", tags=["cards"], summary="Lister les cartes archivées", response_model=CardListResponse)
def list_archived_cards(board_id: int, current_user: User = Depends(get_current_user)):
    cards = _card_service.list_archived_cards(board_id=board_id, user_id=current_user.id)
    return _cards_json(cards)


# ===== ARCHIVES COLONNES =====

@router.patch("/{board_id}/columns/{column_id}/archive", tags=["columns"], summary="Archiver une colonne", response_model=SingleColumnResponse)
async def archive_column(board_id: int, column_id: int, current_user: User = Depends(get_current_user)):
    column = _service.archive_column(board_id=board_id, column_id=column_id, user_id=current_user.id)
    response = _column_json(column)
    await _broadcast(board_id, "column.archived", {"column_id": column_id}, current_user.id)
    return response


@router.patch("/{board_id}/columns/{column_id}/unarchive", tags=["columns"], summary="Restaurer une colonne archivée", response_model=SingleColumnResponse)
async def unarchive_column(board_id: int, column_id: int, current_user: User = Depends(get_current_user)):
    column = _service.unarchive_column(board_id=board_id, column_id=column_id, user_id=current_user.id)
    response = _column_json(column)
    await _broadcast(board_id, "column.restored", _column_data(column), current_user.id)
    return response


@router.get("/{board_id}/archives/columns", tags=["columns"], summary="Lister les colonnes archivées", response_model=ColumnListResponse)
def list_archived_columns(board_id: int, current_user: User = Depends(get_current_user)):
    columns = _service.list_archived_columns(board_id=board_id, user_id=current_user.id)
    return _columns_json(columns)


# ===== ACTIVITE =====

@router.get("/{board_id}/activity", tags=["boards"], summary="Historique d'activité du board", response_model=ActivityListResponse)
def get_board_activity(board_id: int, current_user: User = Depends(get_current_user)):
    _service.get_board(board_id=board_id, user_id=current_user.id)
    activities = _activity_service.get_board_activity(board_id=board_id)
    data = [
        ActivityLogResponse(
            id=a["id"],
            entity_type=a["entity_type"],
            entity_id=a["entity_id"],
            entity_name=a["entity_name"],
            action=a["action"],
            meta=a["meta"],
            created_at=a["created_at"],
            actor=ActorResponse(**a["actor"]),
        )
        for a in activities
    ]
    return _json(ActivityListResponse(data=data))
