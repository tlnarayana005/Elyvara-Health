import json


class TestSignup:
    def test_signup_success(self, client):
        resp = client.post("/auth/signup", json={
            "name": "New User",
            "email": "new@test.com",
            "password": "password123",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["user"]["email"] == "new@test.com"
        assert "password_hash" not in data["user"]

    def test_signup_duplicate_email(self, client, normal_user):
        resp = client.post("/auth/signup", json={
            "name": "Duplicate",
            "email": "alice@test.com",
            "password": "password123",
        })
        assert resp.status_code == 409
        assert "already registered" in resp.get_json()["error"].lower()

    def test_signup_missing_fields(self, client):
        resp = client.post("/auth/signup", json={"email": "x@test.com"})
        assert resp.status_code == 400

    def test_signup_short_password(self, client):
        resp = client.post("/auth/signup", json={
            "name": "Short",
            "email": "short@test.com",
            "password": "abc",
        })
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client, normal_user):
        resp = client.post("/auth/login", json={
            "email": "alice@test.com",
            "password": "alice123",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert data["user"]["email"] == "alice@test.com"

    def test_login_wrong_password(self, client, normal_user):
        resp = client.post("/auth/login", json={
            "email": "alice@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@test.com",
            "password": "pass123",
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/auth/login", json={})
        assert resp.status_code == 400


class TestJWT:
    def test_missing_jwt(self, client):
        resp = client.get("/centres/")
        assert resp.status_code == 401

    def test_invalid_jwt(self, client):
        resp = client.get("/centres/", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert resp.status_code == 401

    def test_malformed_auth_header(self, client):
        resp = client.get("/centres/", headers={
            "Authorization": "Token something"
        })
        assert resp.status_code == 401
