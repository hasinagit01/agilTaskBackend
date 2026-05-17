class TestRegister:
    def test_success(self, client):
        r = client.post("/auth/register", json={"email": "user@example.com", "password": "password123"})
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["email"] == "user@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "password_hash" not in data

    def test_duplicate_email_returns_409(self, client):
        payload = {"email": "dup@example.com", "password": "password123"}
        client.post("/auth/register", json=payload)
        r = client.post("/auth/register", json=payload)
        assert r.status_code == 409

    def test_password_too_short_returns_422(self, client):
        r = client.post("/auth/register", json={"email": "user@example.com", "password": "short"})
        assert r.status_code == 422

    def test_invalid_email_returns_422(self, client):
        r = client.post("/auth/register", json={"email": "not-an-email", "password": "password123"})
        assert r.status_code == 422

    def test_email_is_normalized_to_lowercase(self, client):
        r = client.post("/auth/register", json={"email": "User@Example.COM", "password": "password123"})
        assert r.json()["data"]["email"] == "user@example.com"


class TestLogin:
    def test_success(self, client):
        client.post("/auth/register", json={"email": "login@example.com", "password": "password123"})
        r = client.post("/auth/login", json={"email": "login@example.com", "password": "password123"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in_minutes"] == 30

    def test_wrong_password_returns_401(self, client):
        client.post("/auth/register", json={"email": "pw@example.com", "password": "password123"})
        r = client.post("/auth/login", json={"email": "pw@example.com", "password": "wrongpassword"})
        assert r.status_code == 401

    def test_unknown_email_returns_401(self, client):
        r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
        assert r.status_code == 401

    def test_token_grants_access_to_boards(self, client):
        client.post("/auth/register", json={"email": "boarduser@example.com", "password": "password123"})
        r = client.post("/auth/login", json={"email": "boarduser@example.com", "password": "password123"})
        token = r.json()["data"]["access_token"]
        r = client.get("/boards/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_invalid_token_returns_401(self, client):
        r = client.get("/boards/", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401
