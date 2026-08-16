import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import config
from app.db import init_db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
  db_path = tmp_path / "test.db"

  monkeypatch.setattr(config, "DB_PATH", db_path)

  init_db()

  return db_path
