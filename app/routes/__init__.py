from flask import Flask

from .auth import auth
from .main import main
from .scanner import scanner


def register_routes(app: Flask):
  app.register_blueprint(auth)
  app.register_blueprint(main)
  app.register_blueprint(scanner)
