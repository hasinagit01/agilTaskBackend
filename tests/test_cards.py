def create_board(client, headers, name="Mon board"):
    return client.post("/boards/", json={"name": name}, headers=headers).json()["data"]


def create_column(client, headers, board_id, name="À faire"):
    return client.post(f"/boards/{board_id}/columns/", json={"name": name}, headers=headers).json()["data"]


def create_card(client, headers, board_id, column_id, title="Ma carte", description="Détail"):
    return client.post(
        f"/boards/{board_id}/columns/{column_id}/cards/",
        json={"title": title, "description": description},
        headers=headers,
    )


class TestCards:
    def test_create_success(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        r = create_card(client, auth_headers, board["id"], col["id"])
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["title"] == "Ma carte"
        assert data["description"] == "Détail"
        assert data["column_id"] == col["id"]
        assert data["position"] == 0

    def test_position_auto_increments(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        create_card(client, auth_headers, board["id"], col["id"], title="Carte 1")
        r = create_card(client, auth_headers, board["id"], col["id"], title="Carte 2")
        assert r.json()["data"]["position"] == 1

    def test_list_cards_ordered_by_position(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        create_card(client, auth_headers, board["id"], col["id"], title="Carte A")
        create_card(client, auth_headers, board["id"], col["id"], title="Carte B")
        r = client.get(f"/boards/{board['id']}/columns/{col['id']}/cards/", headers=auth_headers)
        assert r.status_code == 200
        cards = r.json()["data"]
        assert len(cards) == 2
        assert cards[0]["position"] < cards[1]["position"]

    def test_get_card(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        card_id = create_card(client, auth_headers, board["id"], col["id"]).json()["data"]["id"]
        r = client.get(f"/boards/{board['id']}/columns/{col['id']}/cards/{card_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["id"] == card_id

    def test_get_card_not_found(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        r = client.get(f"/boards/{board['id']}/columns/{col['id']}/cards/999", headers=auth_headers)
        assert r.status_code == 404

    def test_update_card(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        card_id = create_card(client, auth_headers, board["id"], col["id"]).json()["data"]["id"]
        r = client.put(
            f"/boards/{board['id']}/columns/{col['id']}/cards/{card_id}",
            json={"title": "Modifié", "description": "Nouvelle desc"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["title"] == "Modifié"

    def test_create_card_with_due_date(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        r = client.post(
            f"/boards/{board['id']}/columns/{col['id']}/cards/",
            json={"title": "Avec deadline", "due_date": "2026-12-31"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["data"]["due_date"] == "2026-12-31"

    def test_move_card_to_another_column(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col_a = create_column(client, auth_headers, board["id"], name="Col A")
        col_b = create_column(client, auth_headers, board["id"], name="Col B")
        card_id = create_card(client, auth_headers, board["id"], col_a["id"]).json()["data"]["id"]
        r = client.patch(
            f"/boards/{board['id']}/columns/{col_a['id']}/cards/{card_id}/move",
            json={"target_column_id": col_b["id"]},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["column_id"] == col_b["id"]

    def test_move_card_to_invalid_column_returns_404(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        card_id = create_card(client, auth_headers, board["id"], col["id"]).json()["data"]["id"]
        r = client.patch(
            f"/boards/{board['id']}/columns/{col['id']}/cards/{card_id}/move",
            json={"target_column_id": 999},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_delete_card(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        card_id = create_card(client, auth_headers, board["id"], col["id"]).json()["data"]["id"]
        r = client.delete(f"/boards/{board['id']}/columns/{col['id']}/cards/{card_id}", headers=auth_headers)
        assert r.status_code == 204

    def test_delete_column_cascades_to_cards(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        create_card(client, auth_headers, board["id"], col["id"])
        client.delete(f"/boards/{board['id']}/columns/{col['id']}", headers=auth_headers)
        # La colonne est supprimée → les cartes n'existent plus
        r = client.get(f"/boards/{board['id']}/columns/{col['id']}/cards/", headers=auth_headers)
        assert r.status_code == 404

    def test_title_too_short_returns_422(self, client, auth_headers):
        board = create_board(client, auth_headers)
        col = create_column(client, auth_headers, board["id"])
        r = create_card(client, auth_headers, board["id"], col["id"], title="x")
        assert r.status_code == 422

    def test_card_on_unknown_column_returns_404(self, client, auth_headers):
        board = create_board(client, auth_headers)
        r = client.get(f"/boards/{board['id']}/columns/999/cards/", headers=auth_headers)
        assert r.status_code == 404
