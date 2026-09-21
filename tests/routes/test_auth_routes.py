from app.services.auth import rate_limit


def test_setup_get_redirects_when_not_first_run(gen_test_client, gen_test_admin):
  response = gen_test_client.get("/auth/setup")

  assert response.status_code == 302
  assert response.headers["Location"].endswith("/")


def test_setup_post_redirects_when_not_first_run(gen_test_client, gen_test_admin):
  response = gen_test_client.post(
    "/auth/setup",
    data={
      "username": "new_admin",
      "display_name": "New Admin",
      "password": "password123",
      "confirm_password": "password123",
    },
  )

  assert response.status_code == 302
  assert response.headers["Location"].endswith("/")


def test_setup_post_invalid_username_shows_error(gen_test_client):
  response = gen_test_client.post(
    "/auth/setup",
    data={
      "username": "ab",
      "display_name": "New Admin",
      "password": "password123",
      "confirm_password": "password123",
    },
  )

  assert response.status_code == 200
  assert "Username must be at least 3 characters" in response.get_data(as_text=True)
  assert "ab" in response.get_data(as_text=True)


def test_setup_post_invalid_password_shows_error(gen_test_client):
  response = gen_test_client.post(
    "/auth/setup",
    data={
      "username": "new_admin",
      "display_name": "New Admin",
      "password": "short",
      "confirm_password": "short",
    },
  )

  assert response.status_code == 200
  assert "Password must be at least 8 characters" in response.get_data(as_text=True)


def test_setup_post_mismatched_passwords_shows_error(gen_test_client):
  response = gen_test_client.post(
    "/auth/setup",
    data={
      "username": "new_admin",
      "display_name": "New Admin",
      "password": "password123",
      "confirm_password": "different",
    },
  )

  assert response.status_code == 200
  assert "Passwords do not match" in response.get_data(as_text=True)


def test_login_post_invalid_credentials_shows_error(gen_test_client, gen_test_admin):
  response = gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": "wrong_password",
    },
  )

  assert response.status_code == 200
  assert "Invalid username or password" in response.get_data(as_text=True)


def test_login_post_archived_user_shows_error(gen_test_client, gen_test_admin):
  import sqlite3

  from werkzeug.security import generate_password_hash

  import config

  connection = sqlite3.connect(config.DB_PATH)

  connection.execute(
    """
    INSERT INTO users (
      username,
      name,
      password_hash,
      created_at,
      updated_at,
      archived_at
    )
    VALUES (?, ?, ?, datetime('now'), datetime('now'), datetime('now'))
    """,
    ("archived_user", "Archived", generate_password_hash("password123")),
  )

  connection.commit()
  connection.close()

  response = gen_test_client.post(
    "/auth/login",
    data={
      "username": "archived_user",
      "password": "password123",
    },
  )

  assert response.status_code == 200
  assert "Invalid username or password" in response.get_data(as_text=True)


def test_login_returns_retry_after_when_rate_limited(
  gen_test_client,
  gen_test_admin,
  monkeypatch,
):
  import sqlite3

  from werkzeug.security import generate_password_hash

  import config

  connection = sqlite3.connect(config.DB_PATH)

  connection.execute(
    """
    INSERT INTO users (
      username,
      name,
      password_hash,
      created_at,
      updated_at
    )
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    """,
    ("restricted_user", "Restricted", generate_password_hash("restricted1")),
  )

  connection.commit()
  connection.close()

  password = "restricted1"

  for _ in range(rate_limit._MAX_FAILURES):
    gen_test_client.post(
      "/auth/login",
      data={
        "username": "restricted_user",
        "password": "wrong-" + password,
      },
    )

  response = gen_test_client.post(
    "/auth/login",
    data={
      "username": "restricted_user",
      "password": "wrong-" + password,
    },
  )

  assert response.status_code == 429
  assert response.headers["Retry-After"] == str(rate_limit._WINDOW_SECONDS)
