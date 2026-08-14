from flask import Flask

from .main import main
from .scanner import scanner


def register_routes(app: Flask):
  app.register_blueprint(main)
  app.register_blueprint(scanner)
