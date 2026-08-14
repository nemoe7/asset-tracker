from flask import Blueprint, redirect, render_template, request, session, url_for

scanner = Blueprint("scanner", __name__, url_prefix="/scanner")


@scanner.route("/")
def index():
  return render_template("scanner.jinja")


@scanner.route("/qrcode", methods=["POST"])
def qrcode():
  value = request.form.get("value")

  session["qr_value"] = value

  return redirect(url_for("scanner.result"))


@scanner.route("/result")
def result():
  value = session.pop("qr_value", None)

  return render_template(
    "qrcode.jinja",
    value=value
  )
