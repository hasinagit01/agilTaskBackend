import json
import logging
from collections import defaultdict

from fastapi import WebSocket

_logger = logging.getLogger(__name__)


class ConnectionManager:
    """Singleton qui maintient les connexions WebSocket par board.

    Chaque board a sa propre liste de WebSocket actifs. Un broadcast envoie
    un payload JSON à tous les clients connectés à ce board et nettoie
    automatiquement les connexions mortes.
    """

    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, board_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[board_id].append(ws)
        _logger.debug("WS connected   board=%d total=%d", board_id, len(self._connections[board_id]))

    def disconnect(self, board_id: int, ws: WebSocket) -> None:
        conns = self._connections.get(board_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(board_id, None)
        _logger.debug("WS disconnected board=%d remaining=%d", board_id, len(conns))

    async def broadcast(self, board_id: int, event: dict) -> None:
        """Envoie `event` (sérialisé en JSON) à tous les clients du board."""
        payload = json.dumps(event, default=str)
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(board_id, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(board_id, ws)


manager = ConnectionManager()
