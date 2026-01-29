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




def login(username: str, password: str):
    response = client.post(
        "/login",
        json={"username": username, "password": password},
    )
    return response


def get_token(username: str, password: str) -> str:
    response = login(username, password)
    assert response.status_code == 200
    return response.json()["access_token"]



def test_login_success():
    response = login("admin", "admin123")
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_password():
    response = login("admin", "wrongpassword")
    assert response.status_code == 401


def test_login_non_existing_user():
    response = login("no_user", "password")
    assert response.status_code == 401



def test_create_user_as_admin():
    token = get_token("admin", "admin123")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "test_user_1",
            "password": "test123",
            "roles": ["ROLE_USER"],
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "test_user_1"


def test_create_user_without_token():
    response = client.post(
        "/users",
        json={
            "username": "test_user_2",
            "password": "test123",
            "roles": ["ROLE_USER"],
        },
    )
    assert response.status_code == 401


def test_create_user_as_non_admin():

    admin_token = get_token("admin", "admin123")

    client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "normal_user",
            "password": "user123",
            "roles": ["ROLE_USER"],
        },
    )


    user_token = get_token("normal_user", "user123")


    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "username": "should_fail",
            "password": "123",
            "roles": ["ROLE_USER"],
        },
    )

    assert response.status_code == 403


# ---------- /user_details ----------
def test_user_details_with_token():
    token = get_token("admin", "admin123")

    response = client.get(
        "/user_details",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert "roles" in response.json()


def test_user_details_without_token():
    response = client.get("/user_details")
    assert response.status_code == 401
