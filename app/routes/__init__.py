from flask import Flask

from .admin import admin
from .auth import auth
from .custom_fields import custom_fields
from .inventory import inventory
from .locations import locations
from .main import main


def register_routes(app: Flask):
  app.register_blueprint(admin)
  app.register_blueprint(auth)
  app.register_blueprint(custom_fields)
  app.register_blueprint(inventory)
  app.register_blueprint(locations)
  app.register_blueprint(main)
