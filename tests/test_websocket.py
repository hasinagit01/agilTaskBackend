"""
Tests pour le ConnectionManager WebSocket et le routeur ws_router.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.websockets import WebSocketDisconnect

from websocket.manager import ConnectionManager


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(coro):
    return asyncio.run(coro)


def _make_ws():
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


def create_board_and_token(client):
    """Inscrit un utilisateur, retourne (token, board_id)."""
    client.post("/auth/register", json={"email": "ws@test.com", "password": "password123"})
    r = client.post("/auth/login",    json={"email": "ws@test.com", "password": "password123"})
    token    = r.json()["data"]["access_token"]
    headers  = {"Authorization": f"Bearer {token}"}
    board_id = client.post("/boards/", json={"name": "WS Board"}, headers=headers).json()["data"]["id"]
    return token, board_id


# ── ConnectionManager — unit tests ────────────────────────────────────────────

class TestConnectionManager:

    def test_connect_accepts_websocket(self):
        manager = ConnectionManager()
        ws = _make_ws()
        run(manager.connect(1, ws))
        ws.accept.assert_called_once()

    def test_connect_adds_to_connections(self):
        manager = ConnectionManager()
        ws = _make_ws()
        run(manager.connect(1, ws))
        assert ws in manager._connections[1]

    def test_disconnect_removes_websocket(self):
        manager = ConnectionManager()
        ws = _make_ws()
        run(manager.connect(1, ws))
        manager.disconnect(1, ws)
        assert 1 not in manager._connections

    def test_disconnect_keeps_other_connections(self):
        manager = ConnectionManager()
        ws1, ws2 = _make_ws(), _make_ws()
        run(manager.connect(1, ws1))
        run(manager.connect(1, ws2))
        manager.disconnect(1, ws1)
        assert ws1 not in manager._connections[1]
        assert ws2 in manager._connections[1]

    def test_disconnect_unknown_ws_does_not_raise(self):
        manager = ConnectionManager()
        ws = _make_ws()
        manager.disconnect(1, ws)  # jamais connecté → pas d'erreur

    def test_broadcast_sends_to_all_connections(self):
        manager = ConnectionManager()
        ws1, ws2 = _make_ws(), _make_ws()
        run(manager.connect(1, ws1))
        run(manager.connect(1, ws2))
        run(manager.broadcast(1, {"type": "card.created"}))
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    def test_broadcast_sends_valid_json(self):
        manager = ConnectionManager()
        ws = _make_ws()
        run(manager.connect(1, ws))
        run(manager.broadcast(1, {"type": "card.created", "data": {"id": 5}}))
        payload = ws.send_text.call_args[0][0]
        parsed  = json.loads(payload)
        assert parsed["type"] == "card.created"
        assert parsed["data"]["id"] == 5

    def test_broadcast_skips_other_boards(self):
        manager = ConnectionManager()
        ws1, ws2 = _make_ws(), _make_ws()
        run(manager.connect(1, ws1))
        run(manager.connect(2, ws2))
        run(manager.broadcast(1, {"type": "test"}))
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_not_called()

    def test_broadcast_empty_board_no_error(self):
        manager = ConnectionManager()
        run(manager.broadcast(99, {"type": "test"}))  # aucune connexion → pas d'erreur

    def test_broadcast_removes_dead_connection(self):
        manager = ConnectionManager()
        ws = _make_ws()
        ws.send_text.side_effect = Exception("broken pipe")
        run(manager.connect(1, ws))
        run(manager.broadcast(1, {"type": "test"}))
        assert 1 not in manager._connections

    def test_broadcast_continues_after_dead_connection(self):
        """Un client mort ne bloque pas les autres."""
        manager = ConnectionManager()
        ws_dead, ws_alive = _make_ws(), _make_ws()
        ws_dead.send_text.side_effect = Exception("broken")
        run(manager.connect(1, ws_dead))
        run(manager.connect(1, ws_alive))
        run(manager.broadcast(1, {"type": "test"}))
        ws_alive.send_text.assert_called_once()


# ── WS Router — tests d'intégration ──────────────────────────────────────────

class TestWsRouter:

    def test_invalid_token_is_rejected(self, client, test_db):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/boards/1?token=invalid_token"):
                pass  # le serveur ferme avec 4001 avant d'accepter

    def test_missing_token_rejects_connection(self, client, test_db):
        """Sans query param ?token=, FastAPI valide en amont et refuse la connexion WS."""
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/boards/1"):  # pas de ?token=
                pass

    def test_no_board_access_is_rejected(self, client, test_db):
        """Utilisateur valide mais board inexistant → 4003."""
        client.post("/auth/register", json={"email": "a@test.com", "password": "password123"})
        r = client.post("/auth/login",    json={"email": "a@test.com", "password": "password123"})
        token = r.json()["data"]["access_token"]
        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/boards/9999?token={token}"):
                pass

    def test_valid_connection_accepted(self, client, test_db):
        token, board_id = create_board_and_token(client)
        # La connexion doit s'établir sans lever d'exception
        with client.websocket_connect(f"/ws/boards/{board_id}?token={token}") as ws:
            ws.close()

    def test_broadcast_reaches_connected_client(self, client, test_db):
        """Un message broadcasté par une mutation HTTP est reçu par le client WS."""
        token, board_id = create_board_and_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        with client.websocket_connect(f"/ws/boards/{board_id}?token={token}") as ws:
            # Créer une colonne déclenche un broadcast "column.created"
            client.post(
                f"/boards/{board_id}/columns/",
                json={"name": "Todo"},
                headers=headers,
            )
            # Le client WS reçoit l'événement
            data = json.loads(ws.receive_text())
            assert data["type"] == "column.created"
            assert data["data"]["name"] == "Todo"
            ws.close()
