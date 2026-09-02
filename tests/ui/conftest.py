import tempfile
import threading
import time
from pathlib import Path

import pytest
from werkzeug.serving import make_server

import config
from app import create_app


@pytest.fixture(scope="session")
def e2e_db(worker_id):
  original_db_path = config.DB_PATH

  with tempfile.TemporaryDirectory(prefix=f"inventory-e2e-{worker_id}-") as temp_dir:
    db_path = Path(temp_dir) / "e2e.db"
    config.DB_PATH = db_path

    try:
      yield db_path
    finally:
      config.DB_PATH = original_db_path


@pytest.fixture(scope="session")
def e2e_app(e2e_db):
  app = create_app()
  app.config.update(
    TESTING=True,
  )

  return app


@pytest.fixture(scope="session")
def live_server(e2e_app):
  server = make_server("127.0.0.1", 0, e2e_app)
  thread = threading.Thread(target=server.serve_forever)
  thread.start()

  yield f"http://127.0.0.1:{server.server_port}"

  server.shutdown()
  thread.join()


@pytest.fixture
def page(page):
  page.set_default_timeout(5_000)
  page.set_default_navigation_timeout(5_000)
  return page


@pytest.fixture(autouse=True)
def reset_e2e_db(e2e_db):
  if e2e_db.exists():
    for _ in range(10):
      try:
        e2e_db.unlink()
        break
      except Exception as e:  # noqa: BLE001
        print(f"Failed to delete {e2e_db}: {e}. Retrying...")
        time.sleep(0.1)
