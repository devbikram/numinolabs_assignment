"""
RBAC and user-management integration tests.
"""
import pytest

from tests.conftest import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    MANAGER_EMAIL,
    MANAGER_PASSWORD,
    auth_headers,
    login,
)


# ---------------------------------------------------------------------------
# Login behaviour
# ---------------------------------------------------------------------------


class TestLogin:
    def test_admin_can_login(self, client, seed_admin):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_manager_can_login(self, client, seed_manager):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD},
        )
        assert resp.status_code == 200

    def test_wrong_password_rejected(self, client, seed_admin):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_inactive_user_cannot_login(self, client, db, seed_manager):
        from models import User

        db.query(User).filter(User.email == MANAGER_EMAIL).update({"is_active": False})
        db.commit()
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD},
        )
        assert resp.status_code == 403

    def test_unauthenticated_request_rejected(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Admin — list users
# ---------------------------------------------------------------------------


class TestListUsers:
    def test_admin_can_list_users(self, client, seed_admin, seed_manager):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = client.get("/api/v1/auth/users", headers=auth_headers(token))
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()["items"]]
        assert ADMIN_EMAIL in emails
        assert MANAGER_EMAIL in emails

    def test_manager_cannot_list_users(self, client, seed_admin, seed_manager):
        token = login(client, MANAGER_EMAIL, MANAGER_PASSWORD)
        resp = client.get("/api/v1/auth/users", headers=auth_headers(token))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_list_users(self, client):
        resp = client.get("/api/v1/auth/users")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Admin — create manager
# ---------------------------------------------------------------------------


class TestCreateUser:
    def test_admin_can_create_manager(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = client.post(
            "/api/v1/auth/users",
            json={"email": "new@library.com", "full_name": "New Manager", "password": "Secure1!"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "new@library.com"
        assert body["role"] == "manager"
        assert body["is_active"] is True

    def test_created_manager_can_login(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        client.post(
            "/api/v1/auth/users",
            json={"email": "new@library.com", "full_name": "New Manager", "password": "Secure1!"},
            headers=auth_headers(token),
        )
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "new@library.com", "password": "Secure1!"},
        )
        assert resp.status_code == 200

    def test_duplicate_email_rejected_with_409(self, client, seed_admin, seed_manager):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = client.post(
            "/api/v1/auth/users",
            json={"email": MANAGER_EMAIL, "full_name": "Duplicate", "password": "Secure1!"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 409

    def test_manager_cannot_create_users(self, client, seed_admin, seed_manager):
        token = login(client, MANAGER_EMAIL, MANAGER_PASSWORD)
        resp = client.post(
            "/api/v1/auth/users",
            json={"email": "another@library.com", "full_name": "Another", "password": "Secure1!"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    def test_short_password_rejected(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = client.post(
            "/api/v1/auth/users",
            json={"email": "short@library.com", "full_name": "Short Pass", "password": "abc"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Admin — activate / deactivate
# ---------------------------------------------------------------------------


class TestUserStatus:
    def test_admin_can_deactivate_manager(self, client, seed_admin, seed_manager):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        users = client.get("/api/v1/auth/users", headers=auth_headers(token)).json()["items"]
        manager = next(u for u in users if u["role"] == "manager")
        resp = client.patch(
            f"/api/v1/auth/users/{manager['id']}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_deactivated_manager_cannot_login(self, client, seed_admin, seed_manager):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        users = client.get("/api/v1/auth/users", headers=auth_headers(token)).json()["items"]
        manager = next(u for u in users if u["role"] == "manager")
        client.patch(
            f"/api/v1/auth/users/{manager['id']}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD},
        )
        assert resp.status_code == 403

    def test_admin_can_reactivate_manager(self, client, seed_admin, seed_manager):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        users = client.get("/api/v1/auth/users", headers=auth_headers(token)).json()["items"]
        manager = next(u for u in users if u["role"] == "manager")
        mgr_id = manager["id"]
        client.patch(
            f"/api/v1/auth/users/{mgr_id}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        resp = client.patch(
            f"/api/v1/auth/users/{mgr_id}/status",
            json={"is_active": True},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    def test_admin_cannot_deactivate_self(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        users = client.get("/api/v1/auth/users", headers=auth_headers(token)).json()["items"]
        admin = next(u for u in users if u["role"] == "admin")
        resp = client.patch(
            f"/api/v1/auth/users/{admin['id']}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        assert resp.status_code == 400

    def test_unknown_user_returns_404(self, client, seed_admin):
        import uuid

        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = client.patch(
            f"/api/v1/auth/users/{uuid.uuid4()}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    def test_manager_cannot_change_user_status(self, client, seed_admin, seed_manager):
        admin_token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        users = client.get("/api/v1/auth/users", headers=auth_headers(admin_token)).json()["items"]
        manager = next(u for u in users if u["role"] == "manager")
        mgr_token = login(client, MANAGER_EMAIL, MANAGER_PASSWORD)
        resp = client.patch(
            f"/api/v1/auth/users/{manager['id']}/status",
            json={"is_active": False},
            headers=auth_headers(mgr_token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Manager — operational library access still works
# ---------------------------------------------------------------------------


class TestManagerOperationalAccess:
    def test_manager_can_access_books(self, client, seed_manager):
        token = login(client, MANAGER_EMAIL, MANAGER_PASSWORD)
        resp = client.get("/api/v1/books/", headers=auth_headers(token))
        # 200 OK is expected (empty list is fine)
        assert resp.status_code == 200

    def test_manager_can_access_authors(self, client, seed_manager):
        token = login(client, MANAGER_EMAIL, MANAGER_PASSWORD)
        resp = client.get("/api/v1/authors/", headers=auth_headers(token))
        assert resp.status_code == 200

    def test_manager_can_access_members(self, client, seed_manager):
        token = login(client, MANAGER_EMAIL, MANAGER_PASSWORD)
        resp = client.get("/api/v1/members/", headers=auth_headers(token))
        assert resp.status_code == 200

    def test_unauthenticated_cannot_access_books(self, client):
        resp = client.get("/api/v1/books/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout / token revocation
# ---------------------------------------------------------------------------


class TestLogout:
    def test_logout_returns_204(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = client.post("/api/v1/auth/logout", headers=auth_headers(token))
        assert resp.status_code == 204

    def test_revoked_token_rejected_on_me(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        client.post("/api/v1/auth/logout", headers=auth_headers(token))
        resp = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 401

    def test_logout_without_token_returns_401(self, client, seed_admin):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401

    def test_logout_revokes_refresh_token(self, client, seed_admin):
        # Obtain a token pair
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        tokens = login_resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Logout, submitting the refresh token in the body
        logout_resp = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers(access_token),
            json={"refresh_token": refresh_token},
        )
        assert logout_resp.status_code == 204

        # Refresh token must now be rejected
        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401

    def test_logout_without_refresh_token_still_revokes_access(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        client.post("/api/v1/auth/logout", headers=auth_headers(token))
        resp = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Password complexity
# ---------------------------------------------------------------------------


class TestPasswordComplexity:
    def _create(self, client, token, email, password):
        return client.post(
            "/api/v1/auth/users",
            json={"email": email, "full_name": "Test User", "password": password},
            headers=auth_headers(token),
        )

    def test_valid_complex_password_accepted(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = self._create(client, token, "complex@lib.com", "Secure1!")
        assert resp.status_code == 201

    def test_no_uppercase_rejected(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = self._create(client, token, "u1@lib.com", "nouppercase1!")
        assert resp.status_code == 422

    def test_no_lowercase_rejected(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = self._create(client, token, "u2@lib.com", "NOLOWER1!")
        assert resp.status_code == 422

    def test_no_digit_rejected(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = self._create(client, token, "u3@lib.com", "NoDigits!")
        assert resp.status_code == 422

    def test_no_special_char_rejected(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = self._create(client, token, "u4@lib.com", "NoSpecial1")
        assert resp.status_code == 422

    def test_password_over_72_bytes_rejected(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        # 73 chars: meets complexity but exceeds bcrypt truncation limit
        long_password = "A1a!" + "x" * 69
        resp = self._create(client, token, "u5@lib.com", long_password)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Refresh token (Issue #14)
# ---------------------------------------------------------------------------


class TestRefreshToken:
    def test_login_returns_refresh_token(self, client, seed_admin):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert resp.status_code == 200
        assert "refresh_token" in resp.json()

    def test_refresh_returns_new_access_token(self, client, seed_admin):
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        refresh_token = login_resp.json()["refresh_token"]
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_access_token_rejected_as_refresh(self, client, seed_admin):
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        access_token = login_resp.json()["access_token"]
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
        assert resp.status_code == 401

    def test_invalid_refresh_token_rejected(self, client, seed_admin):
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage.token.value"})
        assert resp.status_code == 401

    def test_refresh_returns_token_pair(self, client, seed_admin):
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        refresh_token = login_resp.json()["refresh_token"]
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_used_refresh_token_is_revoked(self, client, seed_admin):
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        refresh_token = login_resp.json()["refresh_token"]
        resp1 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp1.status_code == 200
        resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp2.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


class TestGetMe:
    def test_me_returns_current_user_fields(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == ADMIN_EMAIL
        assert body["role"] == "admin"
        assert body["is_active"] is True

    def test_me_response_includes_timestamps(self, client, seed_admin):
        token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "created_at" in body
        assert "updated_at" in body
