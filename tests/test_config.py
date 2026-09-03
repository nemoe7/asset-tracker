import importlib

import config


def _reload_config(monkeypatch, tmp_path, secret_key_env=None):
  monkeypatch.delenv("SECRET_KEY", raising=False)

  if secret_key_env is not None:
    monkeypatch.setenv("SECRET_KEY", secret_key_env)

  monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))

  try:
    return importlib.reload(config)
  finally:
    importlib.reload(config)


def test_secret_key_is_generated_and_persisted(tmp_path, monkeypatch):
  reloaded = _reload_config(monkeypatch, tmp_path)

  key_file = tmp_path / "secret_key"

  assert key_file.exists()
  assert reloaded.SECRET_KEY == key_file.read_text().strip()
  assert reloaded.SECRET_KEY != "secret-key"


def test_secret_key_is_reused_across_restarts(tmp_path, monkeypatch):
  first = _reload_config(monkeypatch, tmp_path).SECRET_KEY
  second = _reload_config(monkeypatch, tmp_path).SECRET_KEY

  assert first == second


def test_secret_key_env_var_takes_precedence(tmp_path, monkeypatch):
  reloaded = _reload_config(
    monkeypatch,
    tmp_path,
    secret_key_env="explicit-key",
  )

  assert reloaded.SECRET_KEY == "explicit-key"

  assert not (tmp_path / "secret_key").exists()


def _create_app(monkeypatch, tmp_path, trust_proxy):
  import config
  from app import create_app

  monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
  monkeypatch.delenv("SECRET_KEY", raising=False)

  if trust_proxy:
    monkeypatch.setenv("TRUST_PROXY", "1")
  else:
    monkeypatch.delenv("TRUST_PROXY", raising=False)

  app = create_app()
  app.config.update(TESTING=True)

  return app


def test_remote_addr_uses_forwarded_for_when_trust_proxy_enabled(
  tmp_path,
  monkeypatch,
):
  app = _create_app(monkeypatch, tmp_path, trust_proxy=True)

  @app.route("/_probe")
  def _probe():
    from flask import request

    return request.remote_addr

  client = app.test_client()

  response = client.get(
    "/_probe",
    headers={"X-Forwarded-For": "203.0.113.7"},
    environ_base={"REMOTE_ADDR": "10.0.0.1"},
  )

  assert response.get_data(as_text=True) == "203.0.113.7"


def test_remote_addr_ignores_forwarded_for_by_default(
  tmp_path,
  monkeypatch,
):
  app = _create_app(monkeypatch, tmp_path, trust_proxy=False)

  @app.route("/_probe")
  def _probe():
    from flask import request

    return request.remote_addr

  client = app.test_client()

  response = client.get(
    "/_probe",
    headers={"X-Forwarded-For": "203.0.113.7"},
    environ_base={"REMOTE_ADDR": "10.0.0.1"},
  )

  assert response.get_data(as_text=True) == "10.0.0.1"
