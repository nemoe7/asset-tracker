import os

from app import create_app

app = create_app()

_DEBUG = os.environ.get("DEBUG", "0").strip().lower() in {"1", "true", "yes"}

if __name__ == "__main__":
  app.run(
    host="0.0.0.0",
    port=5000,
    debug=_DEBUG,
  )
