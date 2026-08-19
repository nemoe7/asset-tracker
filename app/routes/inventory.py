from flask import (
  Blueprint,
  redirect,
  render_template,
  request,
  url_for,
)

from app.auth import login_required
from app.services.inventory import create_item

inventory = Blueprint(
  "inventory",
  __name__,
  url_prefix="/inventory",
)


@inventory.route("", methods=["POST"])
@login_required
def create():
  name = request.form.get("name", "").strip()

  try:
    create_item(name=name)
  except ValueError as error:
    return render_template(
      "index.jinja",
      error=str(error),
      name=name,
      items=[],
      search="",
      page=1,
      total_pages=1,
    )

  return redirect(url_for("main.index"))
