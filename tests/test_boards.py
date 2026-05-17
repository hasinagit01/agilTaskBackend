def create_board(client, headers, name="Mon board"):
    return client.post("/boards/", json={"name": name}, headers=headers)


def create_column(client, headers, board_id, name="À faire"):
    return client.post(f"/boards/{board_id}/columns/", json={"name": name}, headers=headers)


class TestBoards:
    def test_create_success(self, client, auth_headers):
        r = create_board(client, auth_headers)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["name"] == "Mon board"
        assert "id" in data
        assert "owner_id" in data

    def test_list_empty(self, client, auth_headers):
        r = client.get("/boards/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"] == []

    def test_list_returns_created(self, client, auth_headers):
        create_board(client, auth_headers)
        r = client.get("/boards/", headers=auth_headers)
        assert len(r.json()["data"]) == 1

    def test_get_success(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        r = client.get(f"/boards/{board_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["id"] == board_id

    def test_get_not_found(self, client, auth_headers):
        r = client.get("/boards/999", headers=auth_headers)
        assert r.status_code == 404

    def test_update_success(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        r = client.put(f"/boards/{board_id}", json={"name": "Renommé"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "Renommé"

    def test_delete_success(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        r = client.delete(f"/boards/{board_id}", headers=auth_headers)
        assert r.status_code == 204
        r = client.get(f"/boards/{board_id}", headers=auth_headers)
        assert r.status_code == 404

    def test_name_too_short_returns_422(self, client, auth_headers):
        r = create_board(client, auth_headers, name="x")
        assert r.status_code == 422

    def test_unauthenticated_returns_401(self, client):
        r = client.get("/boards/")
        assert r.status_code == 401

    def test_other_user_cannot_access_board(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        # Crée un second utilisateur
        client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
        r2 = client.post("/auth/login", json={"email": "other@example.com", "password": "password123"})
        other_headers = {"Authorization": f"Bearer {r2.json()['data']['access_token']}"}
        r = client.get(f"/boards/{board_id}", headers=other_headers)
        assert r.status_code == 404


class TestColumns:
    def test_create_success(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        r = create_column(client, auth_headers, board_id)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["name"] == "À faire"
        assert data["board_id"] == board_id
        assert data["position"] == 0

    def test_position_auto_increments(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        create_column(client, auth_headers, board_id, name="Col 1")
        r = create_column(client, auth_headers, board_id, name="Col 2")
        assert r.json()["data"]["position"] == 1

    def test_list_columns_ordered_by_position(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        create_column(client, auth_headers, board_id, name="Col A")
        create_column(client, auth_headers, board_id, name="Col B")
        r = client.get(f"/boards/{board_id}/columns/", headers=auth_headers)
        assert r.status_code == 200
        cols = r.json()["data"]
        assert len(cols) == 2
        assert cols[0]["position"] < cols[1]["position"]

    def test_update_column(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        col_id = create_column(client, auth_headers, board_id).json()["data"]["id"]
        r = client.put(f"/boards/{board_id}/columns/{col_id}", json={"name": "En cours"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "En cours"

    def test_delete_column(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        col_id = create_column(client, auth_headers, board_id).json()["data"]["id"]
        r = client.delete(f"/boards/{board_id}/columns/{col_id}", headers=auth_headers)
        assert r.status_code == 204

    def test_column_not_found(self, client, auth_headers):
        board_id = create_board(client, auth_headers).json()["data"]["id"]
        r = client.get(f"/boards/{board_id}/columns/999", headers=auth_headers)
        assert r.status_code == 404

    def test_column_on_unknown_board_returns_404(self, client, auth_headers):
        r = create_column(client, auth_headers, board_id=999)
        assert r.status_code == 404
