import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from services.auth_service import AuthService, decode_token
from services.board_service import BoardService
from services.business_error import BusinessError
from websocket.manager import manager

_logger = logging.getLogger(__name__)
_auth_service = AuthService()
_board_service = BoardService()

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/boards/{board_id}")
async def ws_board(board_id: int, websocket: WebSocket, token: str = Query(...)):
    """Connexion WebSocket temps-réel pour un board.

    Auth : passer le JWT dans le query param `token`.
    Le serveur ferme la connexion avec le code 4001 si le token est invalide
    ou 4003 si l'utilisateur n'est pas membre du board.
    """
    # ── Authentification ──────────────────────────────────────────────────────
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        user = _auth_service.get_user_by_id(user_id)
        if user is None:
            raise BusinessError("Utilisateur introuvable", status_code=401)
    except BusinessError:
        await websocket.close(code=4001)
        return

    # ── Vérification d'accès au board ─────────────────────────────────────────
    try:
        _board_service.get_board(board_id, user_id)
    except BusinessError:
        await websocket.close(code=4003)
        return

    # ── Boucle principale ─────────────────────────────────────────────────────
    await manager.connect(board_id, websocket)
    _logger.info("WS open  board=%d user=%d", board_id, user_id)
    try:
        while True:
            # On ignore les messages entrants (le client peut envoyer un ping)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(board_id, websocket)
        _logger.info("WS close board=%d user=%d", board_id, user_id)
