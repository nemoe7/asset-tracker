import io
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import config


def test_import_requires_login(gen_test_client):
  response = gen_test_client.post("/inventory/import")

  assert response.status_code == 302


def test_import_requires_inventory_import_permission(
  gen_test_client,
  gen_test_admin,
):
  # The permission decorator denies unauthorized users; the existing
  # app-wide behavior raises PermissionDeniedError (unhandled → 500).
  from app.services.exceptions.auth.authorization import PermissionDeniedError

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

  gen_test_client.post(
    "/auth/login",
    data={
      "username": "restricted_user",
      "password": "restricted1",
    },
  )

  with pytest.raises(PermissionDeniedError):
    gen_test_client.post(
      "/inventory/import",
      data={"file": (io.BytesIO(b"name\nAlpha\n"), "items.csv")},
      content_type="multipart/form-data",
    )


def test_import_returns_imported_count(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/inventory/import",
    data={
      "file": (
        io.BytesIO("name,description\nAlpha,First\nBeta,\n".encode("utf-8")),
        "items.csv",
      ),
    },
    content_type="multipart/form-data",
  )

  assert response.status_code == 200
  assert response.get_json() == {"imported_count": 2}


def test_import_invalid_file_returns_400(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/inventory/import",
    data={
      "file": (
        io.BytesIO("description\nFirst\n".encode("utf-8")),
        "items.csv",
      ),
    },
    content_type="multipart/form-data",
  )

  assert response.status_code == 400
  assert "error" in response.get_json()