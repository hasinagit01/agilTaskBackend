"""Tests pour les labels (board-level + attachement aux cartes)."""


def setup_board_with_column_and_card(client, auth_headers):
    board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
    col_id = client.post(f"/boards/{board_id}/columns/", json={"name": "Todo"}, headers=auth_headers).json()["data"]["id"]
    card_id = client.post(
        f"/boards/{board_id}/columns/{col_id}/cards/",
        json={"title": "Carte test"},
        headers=auth_headers,
    ).json()["data"]["id"]
    return board_id, col_id, card_id


class TestBoardLabels:
    def test_create_label(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        r = client.post(
            f"/boards/{board_id}/labels/",
            json={"name": "Bug", "color": "#ef4444"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["name"] == "Bug"
        assert data["color"] == "#ef4444"
        assert data["board_id"] == board_id

    def test_create_label_default_color(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        r = client.post(f"/boards/{board_id}/labels/", json={"name": "Feature"}, headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["data"]["color"] == "#6366f1"

    def test_invalid_color_returns_422(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        r = client.post(f"/boards/{board_id}/labels/", json={"name": "X", "color": "red"}, headers=auth_headers)
        assert r.status_code == 422

    def test_list_labels(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=auth_headers)
        client.post(f"/boards/{board_id}/labels/", json={"name": "Feature", "color": "#22c55e"}, headers=auth_headers)
        r = client.get(f"/boards/{board_id}/labels/", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["data"]) == 2

    def test_update_label(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        label_id = client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=auth_headers).json()["data"]["id"]
        r = client.put(f"/boards/{board_id}/labels/{label_id}", json={"name": "Critical", "color": "#dc2626"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "Critical"

    def test_delete_label(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        label_id = client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=auth_headers).json()["data"]["id"]
        r = client.delete(f"/boards/{board_id}/labels/{label_id}", headers=auth_headers)
        assert r.status_code == 204
        labels = client.get(f"/boards/{board_id}/labels/", headers=auth_headers).json()["data"]
        assert len(labels) == 0

    def test_viewer_cannot_create_label(self, client, auth_headers):
        from tests.test_members import register_and_login
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        viewer_headers = register_and_login(client, "viewer_label@example.com")
        viewer_id = client.post("/boards/", json={"name": "TempBoard"}, headers=viewer_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": viewer_id, "role": "viewer"}, headers=auth_headers)
        r = client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=viewer_headers)
        assert r.status_code == 403


class TestCardLabels:
    def test_attach_label_appears_in_card_response(self, client, auth_headers):
        board_id, col_id, card_id = setup_board_with_column_and_card(client, auth_headers)
        label_id = client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=auth_headers).json()["data"]["id"]

        r = client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/labels/{label_id}", headers=auth_headers)
        assert r.status_code == 204

        card = client.get(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}", headers=auth_headers).json()["data"]
        assert len(card["labels"]) == 1
        assert card["labels"][0]["id"] == label_id
        assert card["labels"][0]["name"] == "Bug"

    def test_detach_label(self, client, auth_headers):
        board_id, col_id, card_id = setup_board_with_column_and_card(client, auth_headers)
        label_id = client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=auth_headers).json()["data"]["id"]
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/labels/{label_id}", headers=auth_headers)

        r = client.delete(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/labels/{label_id}", headers=auth_headers)
        assert r.status_code == 204

        card = client.get(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}", headers=auth_headers).json()["data"]
        assert len(card["labels"]) == 0

    def test_attach_label_twice_returns_409(self, client, auth_headers):
        board_id, col_id, card_id = setup_board_with_column_and_card(client, auth_headers)
        label_id = client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=auth_headers).json()["data"]["id"]
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/labels/{label_id}", headers=auth_headers)
        r = client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/labels/{label_id}", headers=auth_headers)
        assert r.status_code == 409

    def test_delete_label_cascades_to_card(self, client, auth_headers):
        board_id, col_id, card_id = setup_board_with_column_and_card(client, auth_headers)
        label_id = client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=auth_headers).json()["data"]["id"]
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/labels/{label_id}", headers=auth_headers)
        client.delete(f"/boards/{board_id}/labels/{label_id}", headers=auth_headers)

        card = client.get(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}", headers=auth_headers).json()["data"]
        assert len(card["labels"]) == 0

    def test_multiple_labels_on_card(self, client, auth_headers):
        board_id, col_id, card_id = setup_board_with_column_and_card(client, auth_headers)
        label1 = client.post(f"/boards/{board_id}/labels/", json={"name": "Bug", "color": "#ef4444"}, headers=auth_headers).json()["data"]["id"]
        label2 = client.post(f"/boards/{board_id}/labels/", json={"name": "UX", "color": "#3b82f6"}, headers=auth_headers).json()["data"]["id"]
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/labels/{label1}", headers=auth_headers)
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/labels/{label2}", headers=auth_headers)

        card = client.get(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}", headers=auth_headers).json()["data"]
        assert len(card["labels"]) == 2
