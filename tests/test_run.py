import importlib

from flask import Flask


def test_run_module_exposes_app_for_gunicorn(tmp_path, monkeypatch):
  monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
  monkeypatch.setenv("SECRET_KEY", "test-secret-key")

  import config

  importlib.reload(config)
  try:
    run = importlib.import_module("run")
    importlib.reload(run)

    assert isinstance(run.app, Flask)
  finally:
    importlib.reload(config)

