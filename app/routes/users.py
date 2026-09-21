from flask import (
  Blueprint,
  jsonify,
)

from ..services.auth.authentication import login_required
from ..services.auth.authorization import permission_required
from ..services.data.users import get_users

users = Blueprint(
  "users",
  __name__,
  url_prefix="/users",
)


@users.route("", methods=["GET"])
@login_required
@permission_required("users.read")
def index():
  return jsonify(
    [
      {
        "id": user["id"],
        "username": user["username"],
        "name": user["name"],
      }
      for user in get_users()
    ]
  )
