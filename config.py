import os
from pathlib import Path

DB_PATH = Path(os.environ.get("DATABASE_PATH", "data/inventory.db"))
