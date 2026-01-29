import sys
from pathlib import Path
import importlib.util

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

MAIN_PATH = API_DIR / "main.py"
spec = importlib.util.spec_from_file_location("main", MAIN_PATH)
main = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(main)
app = main.app

from fastapi.testclient import TestClient

client = TestClient(app)

def get_admin_token():
    r = client.post("/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    return r.json()["access_token"]

def test_tags_post_create():
    token = get_admin_token()
    r = client.post(
        "/tags",
        headers={"Authorization": f"Bearer {token}"},
        json={"userId": 1, "movieId": 1, "tag": "pytest-tag", "timestamp": 123456},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["tag"] == "pytest-tag"
    assert "id" in body

    # zapisz id do użycia w kolejnych asercjach w tym teście
    tag_id = body["id"]

    # GET item
    r2 = client.get("/tags/" + str(tag_id), headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["id"] == tag_id

def test_tags_put_update_and_delete():
    token = get_admin_token()

    # create tag
    r = client.post(
        "/tags",
        headers={"Authorization": f"Bearer {token}"},
        json={"userId": 2, "movieId": 2, "tag": "to-update", "timestamp": 111},
    )
    assert r.status_code == 201
    tag_id = r.json()["id"]

    # update
    r2 = client.put(
        f"/tags/{tag_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"userId": 2, "movieId": 2, "tag": "updated", "timestamp": 222},
    )
    assert r2.status_code == 200
    assert r2.json()["tag"] == "updated"
    assert r2.json()["timestamp"] == 222

    # delete
    r3 = client.delete(f"/tags/{tag_id}", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 204

    # get after delete -> 404
    r4 = client.get(f"/tags/{tag_id}", headers={"Authorization": f"Bearer {token}"})
    assert r4.status_code == 404
