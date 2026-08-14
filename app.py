from flask import Flask

from routes import register_routes


def create_app():
  app = Flask(__name__)
  app.config.from_object("config")
  register_routes(app)
  return app


if __name__ == "__main__":
  app = create_app()
  app.secret_key = "your-secret-key"
  app.run(host="0.0.0.0", port=5000, debug=True)
