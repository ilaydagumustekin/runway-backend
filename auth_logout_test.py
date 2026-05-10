from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_logout_blacklists_current_token():
    email = f"logout-{uuid4()}@example.com"
    password = "strongpass123"

    with TestClient(app) as client:
        register_response = client.post(
            "/auth/register",
            json={
                "full_name": "Logout Test User",
                "email": email,
                "password": password,
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/auth/login-json",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        before_logout_response = client.get("/users/me", headers=headers)
        assert before_logout_response.status_code == 200

        logout_response = client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == 200

        after_logout_response = client.get("/users/me", headers=headers)
        assert after_logout_response.status_code == 401
