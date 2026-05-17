"""Tests pour le système de positions (drag-and-drop)."""


def create_board(client, headers, name="Board"):
    return client.post("/boards/", json={"name": name}, headers=headers).json()["data"]["id"]


def create_column(client, headers, board_id, name):
    return client.post(f"/boards/{board_id}/columns/", json={"name": name}, headers=headers).json()["data"]


def create_card(client, headers, board_id, col_id, title):
    return client.post(
        f"/boards/{board_id}/columns/{col_id}/cards/",
        json={"title": title},
        headers=headers,
    ).json()["data"]


def get_columns(client, headers, board_id):
    return client.get(f"/boards/{board_id}/columns/", headers=headers).json()["data"]


def get_cards(client, headers, board_id, col_id):
    return client.get(f"/boards/{board_id}/columns/{col_id}/cards/", headers=headers).json()["data"]


class TestColumnPositions:
    def test_columns_get_sequential_positions(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        col_a = create_column(client, auth_headers, board_id, "Todo")
        col_b = create_column(client, auth_headers, board_id, "Doing")
        col_c = create_column(client, auth_headers, board_id, "Done")
        assert col_a["position"] == 0
        assert col_b["position"] == 1
        assert col_c["position"] == 2

    def test_reorder_columns(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        col_a = create_column(client, auth_headers, board_id, "Todo")
        col_b = create_column(client, auth_headers, board_id, "Doing")
        col_c = create_column(client, auth_headers, board_id, "Done")

        # Inverser l'ordre : Done, Doing, Todo
        new_order = [col_c["id"], col_b["id"], col_a["id"]]
        r = client.patch(
            f"/boards/{board_id}/columns/reorder",
            json={"ordered_ids": new_order},
            headers=auth_headers,
        )
        assert r.status_code == 200
        cols = r.json()["data"]
        assert [c["id"] for c in cols] == new_order
        assert [c["position"] for c in cols] == [0, 1, 2]

    def test_reorder_columns_wrong_ids_returns_422(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        create_column(client, auth_headers, board_id, "Todo")
        r = client.patch(
            f"/boards/{board_id}/columns/reorder",
            json={"ordered_ids": [9999]},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_viewer_cannot_reorder_columns(self, client, auth_headers):
        from tests.test_members import register_and_login
        board_id = create_board(client, auth_headers)
        col_a = create_column(client, auth_headers, board_id, "Todo")
        col_b = create_column(client, auth_headers, board_id, "Doing")
        viewer_headers = register_and_login(client, "viewer_reorder@example.com")
        viewer_id = client.post("/boards/", json={"name": "TempBoard"}, headers=viewer_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": viewer_id, "role": "viewer"}, headers=auth_headers)
        r = client.patch(
            f"/boards/{board_id}/columns/reorder",
            json={"ordered_ids": [col_b["id"], col_a["id"]]},
            headers=viewer_headers,
        )
        assert r.status_code == 403


class TestCardPositions:
    def test_cards_get_sequential_positions(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board_id, "Todo")
        card_a = create_card(client, auth_headers, board_id, col["id"], "Carte A")
        card_b = create_card(client, auth_headers, board_id, col["id"], "Carte B")
        card_c = create_card(client, auth_headers, board_id, col["id"], "Carte C")
        assert card_a["position"] == 0
        assert card_b["position"] == 1
        assert card_c["position"] == 2

    def test_reorder_cards_within_column(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board_id, "Todo")
        card_a = create_card(client, auth_headers, board_id, col["id"], "Carte A")
        card_b = create_card(client, auth_headers, board_id, col["id"], "Carte B")
        card_c = create_card(client, auth_headers, board_id, col["id"], "Carte C")

        # Inverser : C, B, A
        new_order = [card_c["id"], card_b["id"], card_a["id"]]
        r = client.patch(
            f"/boards/{board_id}/columns/{col['id']}/cards/reorder",
            json={"ordered_ids": new_order},
            headers=auth_headers,
        )
        assert r.status_code == 200
        cards = r.json()["data"]
        assert [c["id"] for c in cards] == new_order
        assert [c["position"] for c in cards] == [0, 1, 2]

    def test_move_card_to_another_column_adjusts_positions(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        col_a = create_column(client, auth_headers, board_id, "Todo")
        col_b = create_column(client, auth_headers, board_id, "Done")

        card1 = create_card(client, auth_headers, board_id, col_a["id"], "Carte 1")
        card2 = create_card(client, auth_headers, board_id, col_a["id"], "Carte 2")
        card3 = create_card(client, auth_headers, board_id, col_a["id"], "Carte 3")

        # Déplacer card1 (pos=0) vers col_b
        r = client.patch(
            f"/boards/{board_id}/columns/{col_a['id']}/cards/{card1['id']}/move",
            json={"target_column_id": col_b["id"]},
            headers=auth_headers,
        )
        assert r.status_code == 200

        # Dans col_a, card2 et card3 doivent avoir les positions 0 et 1
        remaining = get_cards(client, auth_headers, board_id, col_a["id"])
        assert len(remaining) == 2
        assert remaining[0]["id"] == card2["id"]
        assert remaining[0]["position"] == 0
        assert remaining[1]["id"] == card3["id"]
        assert remaining[1]["position"] == 1

        # Dans col_b, card1 doit être à la position 0
        moved = get_cards(client, auth_headers, board_id, col_b["id"])
        assert len(moved) == 1
        assert moved[0]["id"] == card1["id"]
        assert moved[0]["position"] == 0

    def test_move_card_to_specific_position_in_target_column(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        col_a = create_column(client, auth_headers, board_id, "Todo")
        col_b = create_column(client, auth_headers, board_id, "Done")

        card1 = create_card(client, auth_headers, board_id, col_a["id"], "Carte 1")
        card2 = create_card(client, auth_headers, board_id, col_b["id"], "Carte 2")
        card3 = create_card(client, auth_headers, board_id, col_b["id"], "Carte 3")

        # Déplacer card1 vers col_b à la position 1 (entre card2 et card3)
        client.patch(
            f"/boards/{board_id}/columns/{col_a['id']}/cards/{card1['id']}/move",
            json={"target_column_id": col_b["id"], "position": 1},
            headers=auth_headers,
        )
        cards_b = get_cards(client, auth_headers, board_id, col_b["id"])
        assert len(cards_b) == 3
        assert cards_b[0]["id"] == card2["id"]  # pos 0
        assert cards_b[1]["id"] == card1["id"]  # pos 1
        assert cards_b[2]["id"] == card3["id"]  # pos 2

    def test_move_card_within_same_column(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board_id, "Todo")

        card_a = create_card(client, auth_headers, board_id, col["id"], "Carte A")
        card_b = create_card(client, auth_headers, board_id, col["id"], "Carte B")
        card_c = create_card(client, auth_headers, board_id, col["id"], "Carte C")

        # Déplacer A (pos 0) à la position 2 (fin)
        r = client.patch(
            f"/boards/{board_id}/columns/{col['id']}/cards/{card_a['id']}/move",
            json={"target_column_id": col["id"], "position": 2},
            headers=auth_headers,
        )
        assert r.status_code == 200
        cards = get_cards(client, auth_headers, board_id, col["id"])
        assert cards[0]["id"] == card_b["id"]
        assert cards[1]["id"] == card_c["id"]
        assert cards[2]["id"] == card_a["id"]

    def test_reorder_cards_wrong_ids_returns_422(self, client, auth_headers):
        board_id = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board_id, "Todo")
        create_card(client, auth_headers, board_id, col["id"], "Carte A")
        r = client.patch(
            f"/boards/{board_id}/columns/{col['id']}/cards/reorder",
            json={"ordered_ids": [9999]},
            headers=auth_headers,
        )
        assert r.status_code == 422
