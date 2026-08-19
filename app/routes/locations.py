from flask import Blueprint, redirect, request, url_for

from app.auth import login_required
from app.services.locations import (
  LocationDeletionConfirmationRequired,
  create_location,
  delete_location,
  update_location,
)

locations = Blueprint(
  "locations",
  __name__,
  url_prefix="/locations",
)


@locations.route("", methods=["POST"])
@login_required
def create():
  name = request.form.get("name", "").strip()
  description = request.form.get("description", "").strip() or None

  try:
    create_location(
      name=name,
      description=description,
    )
  except ValueError:
    return redirect(url_for("main.index"))

  return redirect(url_for("main.index"))


@locations.route("/<int:location_id>", methods=["POST"])
@login_required
def update(location_id):
  name = request.form.get("name", "").strip()
  description = request.form.get("description", "").strip() or None

  try:
    update_location(
      location_id,
      name=name,
      description=description,
    )
  except ValueError:
    return redirect(url_for("main.index"))

  return redirect(url_for("main.index"))


@locations.route("/<int:location_id>/delete", methods=["POST"])
@login_required
def delete(location_id):
  confirm = request.form.get("confirm") == "1"

  try:
    delete_location(
      location_id,
      confirm=confirm,
    )
  except LocationDeletionConfirmationRequired:
    return redirect(url_for("main.index"))

  return redirect(url_for("main.index"))
