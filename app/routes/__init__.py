from flask import Flask

from .admin import admin
from .auth import auth
from .backups import backups
from .custom_fields import custom_fields
from .export_templates import export_templates
from .inventory import inventory
from .locations import locations
from .main import main
from .users import users


def register_routes(app: Flask):
  app.register_blueprint(admin)
  app.register_blueprint(auth)
  app.register_blueprint(backups)
  app.register_blueprint(custom_fields)
  app.register_blueprint(export_templates)
  app.register_blueprint(inventory)
  app.register_blueprint(locations)
  app.register_blueprint(main)
  app.register_blueprint(users)
