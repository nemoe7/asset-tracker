from flask import (
  Blueprint,
  jsonify,
  redirect,
  request,
  url_for,
)

from ..services.constants import UNSET as _UNSET
from ..services.data.locations import (
  create_location,
  delete_location,
  get_location,
  get_locations,
  update_location,
)
from ..services.exceptions.data.common import InvalidInputError
from ..services.exceptions.data.locations import (
  LocationAlreadyExistsError,
  LocationDeletionConfirmationRequired,
  LocationNotFoundError,
)
from .auth import login_required

locations = Blueprint(
  "locations",
  __name__,
  url_prefix="/locations",
)


@locations.route("", methods=["GET"])
@login_required
def index():
  return jsonify([dict(location) for location in get_locations()])


@locations.route("", methods=["POST"])
@login_required
def create():
  name = request.form.get("name", "").strip()
  description = request.form.get("description")

  try:
    location_id = create_location(
      name=name,
      description=description,
    )
  except InvalidInputError as error:
    return jsonify({"error": str(error)}), 400
  except LocationAlreadyExistsError as error:
    return jsonify({"error": str(error)}), 400

  if request.headers.get("Accept") == "application/json":
    return jsonify(
      {
        "id": location_id,
        "name": name,
        "description": description,
      }
    )

  return redirect(url_for("main.index"))


@locations.route("/<int:location_id>", methods=["GET"])
@login_required
def get(location_id):
  location = get_location(location_id)

  if location is None:
    return jsonify({"error": "Location does not exist"}), 404

  return jsonify(dict(location))


@locations.route("/<int:location_id>", methods=["POST"])
@login_required
def update(location_id):
  name = request.form.get("name", _UNSET)
  description = request.form.get("description", _UNSET)

  if name is not _UNSET:
    name = name.strip()

  try:
    update_location(
      location_id,
      name=name,
      description=description,
    )
  except InvalidInputError as error:
    return jsonify({"error": str(error)}), 400
  except LocationAlreadyExistsError as error:
    return jsonify({"error": str(error)}), 400
  except LocationNotFoundError as error:
    return jsonify({"error": str(error)}), 404

  if request.headers.get("Accept") == "application/json":
    updated = get_location(location_id)
    return jsonify(dict(updated))

  return redirect(url_for("main.index"))


@locations.route("/<int:location_id>/delete", methods=["POST"])
@login_required
def delete(location_id):
  if get_location(location_id) is None:
    return jsonify({"error": "Location does not exist"}), 404

  confirm = request.form.get("confirm") == "true"

  try:
    delete_location(
      location_id,
      confirm=confirm,
    )
  except LocationDeletionConfirmationRequired as error:
    return jsonify({"error": str(error)}), 400

  if request.headers.get("Accept") == "application/json":
    return jsonify({"deleted": True, "id": location_id})

  return redirect(url_for("main.index"))
