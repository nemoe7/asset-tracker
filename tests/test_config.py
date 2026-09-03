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
