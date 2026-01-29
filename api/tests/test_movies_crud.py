from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)


def get_admin_token():
    r = client.post("/login", json={"username": "admin", "password": "admin123"})
    return r.json()["access_token"]


def test_create_movie():
    token = get_admin_token()
    movie_id = 999000

    r = client.post(
        "/movies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "movieId": movie_id,
            "title": "Test Movie",
            "genres": "Drama"
        },
    )

    assert r.status_code == 201
    assert r.json()["movieId"] == movie_id


def test_get_movie():
    token = get_admin_token()

    r = client.get(
        "/movies/999000",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 200
    assert r.json()["title"] == "Test Movie"


def test_update_movie():
    token = get_admin_token()

    r = client.put(
        "/movies/999000",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Title",
            "genres": "Comedy"
        },
    )

    assert r.status_code == 200
    assert r.json()["title"] == "Updated Title"


def test_delete_movie():
    token = get_admin_token()

    r = client.delete(
        "/movies/999000",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 204


def test_get_deleted_movie():
    token = get_admin_token()

    r = client.get(
        "/movies/999000",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 404
