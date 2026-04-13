"""
Integration tests for the /categories endpoints.
Covers CRUD, 404/409 error paths, case-insensitive name uniqueness, and pagination.
"""
import uuid

import pytest

from tests.conftest import MANAGER_EMAIL, MANAGER_PASSWORD, auth_headers, login


@pytest.fixture()
def tok(client, seed_manager):
    return login(client, MANAGER_EMAIL, MANAGER_PASSWORD)


def _create(client, tok, name="Fiction"):
    return client.post(
        "/api/v1/categories/",
        json={"name": name},
        headers=auth_headers(tok),
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreateCategory:
    def test_success_returns_201(self, client, tok):
        resp = _create(client, tok)
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Fiction"
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_exact_duplicate_returns_409(self, client, tok):
        _create(client, tok, "Fiction")
        resp = _create(client, tok, "Fiction")
        assert resp.status_code == 409

    def test_case_insensitive_duplicate_returns_409(self, client, tok):
        _create(client, tok, "Fiction")
        resp = _create(client, tok, "fiction")
        assert resp.status_code == 409

    def test_mixed_case_duplicate_returns_409(self, client, tok):
        _create(client, tok, "Science Fiction")
        resp = _create(client, tok, "SCIENCE FICTION")
        assert resp.status_code == 409

    def test_different_name_succeeds(self, client, tok):
        _create(client, tok, "Fiction")
        resp = _create(client, tok, "Non-Fiction")
        assert resp.status_code == 201

    def test_missing_name_returns_422(self, client, tok):
        resp = client.post("/api/v1/categories/", json={}, headers=auth_headers(tok))
        assert resp.status_code == 422

    def test_empty_name_returns_422(self, client, tok):
        resp = client.post("/api/v1/categories/", json={"name": ""}, headers=auth_headers(tok))
        assert resp.status_code == 422

    def test_unauthenticated_returns_401(self, client):
        resp = client.post("/api/v1/categories/", json={"name": "Fiction"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class TestListCategories:
    def test_empty_returns_paginated_response(self, client, tok):
        resp = client.get("/api/v1/categories/", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_lists_created_categories(self, client, tok):
        _create(client, tok, "Fiction")
        _create(client, tok, "Science")
        resp = client.get("/api/v1/categories/", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        names = {c["name"] for c in body["items"]}
        assert names == {"Fiction", "Science"}

    def test_categories_ordered_by_name(self, client, tok):
        _create(client, tok, "Zebra")
        _create(client, tok, "Alpha")
        _create(client, tok, "Mango")
        resp = client.get("/api/v1/categories/", headers=auth_headers(tok))
        names = [c["name"] for c in resp.json()["items"]]
        assert names == sorted(names)

    def test_pagination_skip_and_limit(self, client, tok):
        for name in ["Alpha", "Beta", "Gamma", "Delta"]:
            _create(client, tok, name)
        resp = client.get("/api/v1/categories/?skip=2&limit=2", headers=auth_headers(tok))
        body = resp.json()
        assert body["total"] == 4
        assert len(body["items"]) == 2

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/v1/categories/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


class TestGetCategory:
    def test_returns_category(self, client, tok):
        cat_id = _create(client, tok, "History").json()["id"]
        resp = client.get(f"/api/v1/categories/{cat_id}", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["name"] == "History"

    def test_unknown_id_returns_404(self, client, tok):
        resp = client.get(f"/api/v1/categories/{uuid.uuid4()}", headers=auth_headers(tok))
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"/api/v1/categories/{uuid.uuid4()}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdateCategory:
    def test_rename_succeeds(self, client, tok):
        cat_id = _create(client, tok, "Old Name").json()["id"]
        resp = client.patch(
            f"/api/v1/categories/{cat_id}",
            json={"name": "New Name"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_rename_to_own_name_is_allowed(self, client, tok):
        cat_id = _create(client, tok, "Fiction").json()["id"]
        resp = client.patch(
            f"/api/v1/categories/{cat_id}",
            json={"name": "Fiction"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fiction"

    def test_rename_to_existing_name_returns_409(self, client, tok):
        _create(client, tok, "Fiction")
        other_id = _create(client, tok, "Science").json()["id"]
        resp = client.patch(
            f"/api/v1/categories/{other_id}",
            json={"name": "Fiction"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 409

    def test_rename_case_variant_of_existing_returns_409(self, client, tok):
        _create(client, tok, "Fiction")
        other_id = _create(client, tok, "Science").json()["id"]
        resp = client.patch(
            f"/api/v1/categories/{other_id}",
            json={"name": "FICTION"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 409

    def test_unknown_id_returns_404(self, client, tok):
        resp = client.patch(
            f"/api/v1/categories/{uuid.uuid4()}",
            json={"name": "Anything"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        resp = client.patch(f"/api/v1/categories/{uuid.uuid4()}", json={"name": "X"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDeleteCategory:
    def test_delete_returns_200_with_message(self, client, tok):
        cat_id = _create(client, tok, "ToDelete").json()["id"]
        resp = client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["message"] == "Category deleted successfully"

    def test_deleted_category_no_longer_retrievable(self, client, tok):
        cat_id = _create(client, tok, "Gone").json()["id"]
        client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers(tok))
        resp = client.get(f"/api/v1/categories/{cat_id}", headers=auth_headers(tok))
        assert resp.status_code == 404

    def test_same_name_can_be_reused_after_delete(self, client, tok):
        cat_id = _create(client, tok, "Temporary").json()["id"]
        client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers(tok))
        resp = _create(client, tok, "Temporary")
        assert resp.status_code == 201

    def test_unknown_id_returns_404(self, client, tok):
        resp = client.delete(
            f"/api/v1/categories/{uuid.uuid4()}", headers=auth_headers(tok)
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        resp = client.delete(f"/api/v1/categories/{uuid.uuid4()}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestCategorySearch:
    def test_search_returns_matching_categories(self, client, tok):
        _create(client, tok, "Science Fiction")
        _create(client, tok, "Non-Fiction")
        _create(client, tok, "History")

        resp = client.get("/api/v1/categories/?search=fiction", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        names = [item["name"] for item in body["items"]]
        assert "Science Fiction" in names
        assert "Non-Fiction" in names
        assert "History" not in names

    def test_search_is_case_insensitive(self, client, tok):
        _create(client, tok, "Biography")
        resp = client.get("/api/v1/categories/?search=BIOG", headers=auth_headers(tok))
        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()["items"]]
        assert "Biography" in names

    def test_search_no_match_returns_empty(self, client, tok):
        _create(client, tok, "Mystery")
        resp = client.get("/api/v1/categories/?search=zzznomatch", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_no_search_param_returns_all(self, client, tok):
        _create(client, tok, "Travel")
        _create(client, tok, "Cooking")
        resp = client.get("/api/v1/categories/", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2
