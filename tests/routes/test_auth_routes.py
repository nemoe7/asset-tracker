from app.services.auth import rate_limit


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
