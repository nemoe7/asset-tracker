import json

import pytest

DEFAULT_SCHEDULE = {"type": "weekly", "day": 6, "time": "03:00"}


def test_get_backup_config_returns_config(gen_test_admin_client):
  response = gen_test_admin_client.get("/backups/config")
  assert response.status_code == 200
  body = response.get_json()
  assert body["enabled"] is False
  assert body["schedule"] == DEFAULT_SCHEDULE


def login_restricted_user(gen_test_client):
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

  gen_test_client.post(
    "/auth/login",
    data={"username": "restricted_user", "password": "restricted1"},
  )
  return gen_test_client


def test_get_backup_config_requires_permission(gen_test_client):
  login_restricted_user(gen_test_client)
  response = gen_test_client.get("/backups/config")
  assert response.status_code == 403


def test_put_backup_config_updates_settings(gen_test_admin_client):
  response = gen_test_admin_client.put(
    "/backups/config",
    json={
      "enabled": True,
      "schedule": {"type": "monthly", "day": 15, "time": "04:30"},
    },
  )
  assert response.status_code == 200
  body = response.get_json()
  assert body["enabled"] is True
  assert body["schedule"] == {"type": "monthly", "day": 15, "time": "04:30"}


def test_put_backup_config_rejects_invalid_schedule(gen_test_admin_client):
  response = gen_test_admin_client.put(
    "/backups/config",
    json={"enabled": True, "schedule": {"type": "hourly"}},
  )
  assert response.status_code == 400


def test_put_backup_config_requires_permission(gen_test_client):
  login_restricted_user(gen_test_client)
  response = gen_test_client.put("/backups/config", json={"enabled": True})
  assert response.status_code == 403


def test_run_now_executes_backup(gen_test_admin_client, tmp_path, monkeypatch):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  response = gen_test_admin_client.post("/backups/run-now")
  assert response.status_code == 200
  body = response.get_json()
  assert body["scheduled_at"] is None
  assert body["path"] is not None
