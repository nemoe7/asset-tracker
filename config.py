import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / ".data/inventory.db"))


def _load_secret_key():
  from_environment = os.environ.get("SECRET_KEY")

  if from_environment:
    return from_environment

  key_file = DB_PATH.parent / "secret_key"

  if key_file.exists():
    return key_file.read_text().strip()

  key = secrets.token_hex(32)

  temporary_file = key_file.with_suffix(".tmp")
  temporary_file.write_text(key)
  os.replace(temporary_file, key_file)

  return key


SECRET_KEY = _load_secret_key()
