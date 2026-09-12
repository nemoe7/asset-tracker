import sqlite3
import time
import uuid

import config

_TARGET_SECONDS = 1.0
_SEED_COUNT = 10_000


def test_inventory_fragment_responds_within_target(gen_test_admin_client):
  connection = sqlite3.connect(config.DB_PATH)

  connection.executemany(
    """
    INSERT INTO inventory_items (
      id,
      name,
      created_at,
      updated_at
    )
    VALUES (?, ?, datetime('now'), datetime('now'))
    """,
    ((str(uuid.uuid4()), f"Asset {index:05d}") for index in range(_SEED_COUNT)),
  )

  connection.commit()
  connection.close()

  start = time.perf_counter()

  response = gen_test_admin_client.get("/inventory/fragment")

  elapsed = time.perf_counter() - start

  assert response.status_code == 200
  # PER-001 target: a 10k-asset listing renders server-side in < 1 s.
  assert elapsed < _TARGET_SECONDS
