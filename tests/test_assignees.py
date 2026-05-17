"""Tests pour les assignees (affectation de membres à une carte)."""
from tests.test_members import register_and_login


def setup(client, auth_headers):
    board_id = client.post("/boards/", json={"name": "Board"}, headers=auth_headers).json()["data"]["id"]
    col_id = client.post(f"/boards/{board_id}/columns/", json={"name": "Todo"}, headers=auth_headers).json()["data"]["id"]
    card_id = client.post(
        f"/boards/{board_id}/columns/{col_id}/cards/",
        json={"title": "Carte test"},
        headers=auth_headers,
    ).json()["data"]["id"]
    return board_id, col_id, card_id


class TestAssignees:
    def test_add_assignee_appears_in_card_response(self, client, auth_headers):
        board_id, col_id, card_id = setup(client, auth_headers)
        member_headers = register_and_login(client, "assignee1@example.com")
        member_id = client.post("/boards/", json={"name": "TempBoard"}, headers=member_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": member_id, "role": "member"}, headers=auth_headers)

        r = client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/assignees/{member_id}", headers=auth_headers)
        assert r.status_code == 204

        card = client.get(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}", headers=auth_headers).json()["data"]
        assert len(card["assignees"]) == 1
        assert card["assignees"][0]["user_id"] == member_id

    def test_remove_assignee(self, client, auth_headers):
        board_id, col_id, card_id = setup(client, auth_headers)
        member_headers = register_and_login(client, "assignee2@example.com")
        member_id = client.post("/boards/", json={"name": "TempBoard"}, headers=member_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": member_id, "role": "member"}, headers=auth_headers)
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/assignees/{member_id}", headers=auth_headers)

        r = client.delete(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/assignees/{member_id}", headers=auth_headers)
        assert r.status_code == 204

        card = client.get(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}", headers=auth_headers).json()["data"]
        assert len(card["assignees"]) == 0

    def test_assign_non_member_returns_404(self, client, auth_headers):
        board_id, col_id, card_id = setup(client, auth_headers)
        stranger_headers = register_and_login(client, "stranger_assign@example.com")
        stranger_id = client.post("/boards/", json={"name": "TempBoard"}, headers=stranger_headers).json()["data"]["owner_id"]

        r = client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/assignees/{stranger_id}", headers=auth_headers)
        assert r.status_code == 404

    def test_assign_twice_returns_409(self, client, auth_headers):
        board_id, col_id, card_id = setup(client, auth_headers)
        member_headers = register_and_login(client, "assignee3@example.com")
        member_id = client.post("/boards/", json={"name": "TempBoard"}, headers=member_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": member_id, "role": "member"}, headers=auth_headers)
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/assignees/{member_id}", headers=auth_headers)

        r = client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/assignees/{member_id}", headers=auth_headers)
        assert r.status_code == 409

    def test_multiple_assignees_on_card(self, client, auth_headers):
        board_id, col_id, card_id = setup(client, auth_headers)
        m1_headers = register_and_login(client, "assignee4@example.com")
        m1_id = client.post("/boards/", json={"name": "TempBoard"}, headers=m1_headers).json()["data"]["owner_id"]
        m2_headers = register_and_login(client, "assignee5@example.com")
        m2_id = client.post("/boards/", json={"name": "TempBoard"}, headers=m2_headers).json()["data"]["owner_id"]
        client.post(f"/boards/{board_id}/members/", json={"user_id": m1_id, "role": "member"}, headers=auth_headers)
        client.post(f"/boards/{board_id}/members/", json={"user_id": m2_id, "role": "member"}, headers=auth_headers)
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/assignees/{m1_id}", headers=auth_headers)
        client.post(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}/assignees/{m2_id}", headers=auth_headers)

        card = client.get(f"/boards/{board_id}/columns/{col_id}/cards/{card_id}", headers=auth_headers).json()["data"]
        assert len(card["assignees"]) == 2

    def test_card_with_due_date(self, client, auth_headers):
        board_id, col_id, _ = setup(client, auth_headers)
        r = client.post(
            f"/boards/{board_id}/columns/{col_id}/cards/",
            json={"title": "Deadline card", "due_date": "2026-12-31"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["data"]["due_date"] == "2026-12-31"
