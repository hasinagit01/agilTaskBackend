def register_and_login(client, email, password="password123"):
    client.post("/auth/register", json={"email": email, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}


def get_user_id(client, headers):
    client.post("/boards/", json={"name": "TempBoard"}, headers=headers)
    r = client.get("/boards/", headers=headers)
    return r.json()["data"][0]["owner_id"]


class TestMemberManagement:
    def test_owner_listed_after_create(self, client, auth_headers):
        r = client.post("/boards/", json={"name": "Board test"}, headers=auth_headers)
        board_id = r.json()["data"]["id"]
        r = client.get(f"/boards/{board_id}/members/", headers=auth_headers)
        assert r.status_code == 200
        members = r.json()["data"]
        assert len(members) == 1
        assert members[0]["role"] == "owner"

    def test_add_member(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        other_headers = register_and_login(client, "member@example.com")
        other_id = client.post("/boards/", json={"name": "TempBoard"}, headers=other_headers).json()["data"]["owner_id"]
        r = client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "member"}, headers=auth_headers)
        assert r.status_code == 204
        members = client.get(f"/boards/{board_id}/members/", headers=auth_headers).json()["data"]
        assert len(members) == 2
        roles = {m["user_id"]: m["role"] for m in members}
        assert roles[other_id] == "member"

    def test_member_can_see_board(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        other_headers = register_and_login(client, "viewer@example.com")
        other_id = client.post("/boards/", json={"name": "TempBoard"}, headers=other_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "viewer"}, headers=auth_headers)
        r = client.get(f"/boards/{board_id}", headers=other_headers)
        assert r.status_code == 200

    def test_viewer_cannot_create_column(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        other_headers = register_and_login(client, "viewer2@example.com")
        other_id = client.post("/boards/", json={"name": "TempBoard"}, headers=other_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "viewer"}, headers=auth_headers)
        r = client.post(f"/boards/{board_id}/columns/", json={"name": "Col"}, headers=other_headers)
        assert r.status_code == 403

    def test_member_can_create_column_and_card(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        other_headers = register_and_login(client, "member2@example.com")
        other_id = client.post("/boards/", json={"name": "TempBoard"}, headers=other_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "member"}, headers=auth_headers)
        r = client.post(f"/boards/{board_id}/columns/", json={"name": "Col"}, headers=other_headers)
        assert r.status_code == 201
        col_id = r.json()["data"]["id"]
        r = client.post(f"/boards/{board_id}/columns/{col_id}/cards/", json={"title": "Ma carte"}, headers=other_headers)
        assert r.status_code == 201

    def test_non_member_cannot_access_board(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        stranger_headers = register_and_login(client, "stranger@example.com")
        r = client.get(f"/boards/{board_id}", headers=stranger_headers)
        assert r.status_code == 404

    def test_non_owner_cannot_add_member(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        member_headers = register_and_login(client, "mem@example.com")
        member_id = client.post("/boards/", json={"name": "TempBoard"}, headers=member_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": member_id, "role": "member"}, headers=auth_headers)
        stranger_headers = register_and_login(client, "stranger2@example.com")
        stranger_id = client.post("/boards/", json={"name": "TempBoard"}, headers=stranger_headers).json()["data"]["owner_id"]
        r = client.post(f"/boards/{board_id}/members/", json={"user_id": stranger_id, "role": "member"}, headers=member_headers)
        assert r.status_code == 403

    def test_duplicate_member_returns_409(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        other_headers = register_and_login(client, "dup@example.com")
        other_id = client.post("/boards/", json={"name": "TempBoard"}, headers=other_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "member"}, headers=auth_headers)
        r = client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "viewer"}, headers=auth_headers)
        assert r.status_code == 409

    def test_update_member_role(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        other_headers = register_and_login(client, "upd@example.com")
        other_id = client.post("/boards/", json={"name": "TempBoard"}, headers=other_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "member"}, headers=auth_headers)
        r = client.put(f"/boards/{board_id}/members/{other_id}", json={"role": "viewer"}, headers=auth_headers)
        assert r.status_code == 204

    def test_remove_member(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
        other_headers = register_and_login(client, "rem@example.com")
        other_id = client.post("/boards/", json={"name": "TempBoard"}, headers=other_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "member"}, headers=auth_headers)
        r = client.delete(f"/boards/{board_id}/members/{other_id}", headers=auth_headers)
        assert r.status_code == 204
        members = client.get(f"/boards/{board_id}/members/", headers=auth_headers).json()["data"]
        assert len(members) == 1

    def test_board_appears_in_member_list(self, client, auth_headers):
        board_id = client.post("/boards/", json={"name": "Shared"}, headers=auth_headers).json()["data"]["id"]
        other_headers = register_and_login(client, "shareduser@example.com")
        other_id = client.post("/boards/", json={"name": "TempBoard"}, headers=other_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": other_id, "role": "viewer"}, headers=auth_headers)
        r = client.get("/boards/", headers=other_headers)
        board_ids = [b["id"] for b in r.json()["data"]]
        assert board_id in board_ids
