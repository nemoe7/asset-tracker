from flask import Flask

from .auth import auth
from .inventory import inventory
from .locations import locations
from .main import main
from .scanner import scanner


def register_routes(app: Flask):
  app.register_blueprint(auth)
  app.register_blueprint(inventory)
  app.register_blueprint(locations)
  app.register_blueprint(main)
  app.register_blueprint(scanner)
