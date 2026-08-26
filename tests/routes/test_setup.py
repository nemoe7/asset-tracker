from app.services.data.db import get_db
from app.services.data.users import get_user_by_username


def test_setup_page_is_rendered(test_client):
  response = test_client.get("/auth/setup")

  assert response.status_code == 200


def test_setup_page_redirects_after_first_run(test_admin, test_client):
  response = test_client.get("/auth/setup")

  assert response.status_code == 302
  assert response.location.endswith("/")


def test_setup_creates_initial_admin(test_client):
  response = test_client.post(
    "/auth/setup",
    data={
      "username": "admin",
      "display_name": "Administrator",
      "password": "password123",
      "confirm_password": "password123",
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/")

  user = get_user_by_username("admin")

  assert user is not None
  assert user["name"] == "Administrator"

  connection = get_db()

  try:
    role = connection.execute(
      """
      SELECT r.name
      FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = ?
      """,
      (user["id"],),
    ).fetchone()
  finally:
    connection.close()

  assert role is not None
  assert role["name"] == "Admin"


def test_setup_logs_initial_admin_in(test_client):
  response = test_client.post(
    "/auth/setup",
    data={
      "username": "admin",
      "display_name": "Administrator",
      "password": "password123",
      "confirm_password": "password123",
    },
  )

  assert response.status_code == 302

  with test_client.session_transaction() as session:
    assert session["user_id"] is not None


def test_setup_updates_first_run_state(test_client, test_app):
  response = test_client.post(
    "/auth/setup",
    data={
      "username": "admin",
      "display_name": "Administrator",
      "password": "password123",
      "confirm_password": "password123",
    },
  )

  assert response.status_code == 302
  assert test_app.config["FIRST_RUN"] is False


def test_setup_rejects_password_mismatch(test_client):
  response = test_client.post(
    "/auth/setup",
    data={
      "username": "admin",
      "display_name": "Administrator",
      "password": "password123",
      "confirm_password": "different123",
    },
  )

  assert response.status_code == 200
  assert b"Passwords do not match." in response.data
  assert get_user_by_username("admin") is None


def test_setup_rejects_invalid_username(test_client):
  response = test_client.post(
    "/auth/setup",
    data={
      "username": "a",
      "display_name": "Administrator",
      "password": "password123",
      "confirm_password": "password123",
    },
  )

  assert response.status_code == 200
  assert get_user_by_username("a") is None


def test_setup_rejects_invalid_password(test_client):
  response = test_client.post(
    "/auth/setup",
    data={
      "username": "admin",
      "display_name": "Administrator",
      "password": "short",
      "confirm_password": "short",
    },
  )

  assert response.status_code == 200
  assert get_user_by_username("admin") is None
