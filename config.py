import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PORT = int(os.environ.get("PORT", "5000"))
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "data/inventory.db"))
