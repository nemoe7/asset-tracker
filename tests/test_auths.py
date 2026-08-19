from flask import Flask

from app.auth import login_required
from app.context import (
  get_current_user,
  reset_current_user,
  set_current_user,
)
from app.db import get_db
from app.routes.auth import auth


def _create_test_app():
  app = Flask(__name__)
  app.secret_key = "test-secret-key"

  app.register_blueprint(auth)

  @app.route("/protected")
  @login_required
  def protected():
    return str(get_current_user())

  return app


def test_login_required_redirects_without_session():
  app = _create_test_app()

  with app.test_client() as client:
    response = client.get("/protected")

  assert response.status_code == 302
  assert response.location.endswith("/auth/login")


def test_login_required_allows_valid_session(
  authenticated_test_user,
):
  app = _create_test_app()

  with app.test_client() as client:
    with client.session_transaction() as session:
      session["user_id"] = authenticated_test_user

    response = client.get("/protected")

  assert response.status_code == 200
  assert response.data == str(authenticated_test_user).encode()


def test_login_required_clears_session_for_missing_user(test_db):
  app = _create_test_app()

  with app.test_client() as client:
    with client.session_transaction() as session:
      session["user_id"] = 999999

    response = client.get("/protected")

    assert response.status_code == 302

    with client.session_transaction() as session:
      assert "user_id" not in session


def test_login_required_clears_session_for_archived_user(
  test_db,
  authenticated_test_user,
):
  connection = get_db(test_db)

  try:
    connection.execute(
      """
      UPDATE users
      SET archived_at = datetime('now')
      WHERE id = ?
      """,
      (authenticated_test_user,),
    )
    connection.commit()
  finally:
    connection.close()

  app = _create_test_app()

  with app.test_client() as client:
    with client.session_transaction() as session:
      session["user_id"] = authenticated_test_user

    response = client.get("/protected")

    assert response.status_code == 302

    with client.session_transaction() as session:
      assert "user_id" not in session


def test_login_required_sets_current_user(
  authenticated_test_user,
):
  app = _create_test_app()

  with app.test_client() as client:
    with client.session_transaction() as session:
      session["user_id"] = authenticated_test_user

    response = client.get("/protected")

  assert response.status_code == 200
  assert response.data == str(authenticated_test_user).encode()


def test_login_required_restores_previous_current_user(
  authenticated_test_user,
):
  app = _create_test_app()

  previous_user = 999

  token = set_current_user(previous_user)

  try:
    with app.test_client() as client:
      with client.session_transaction() as session:
        session["user_id"] = authenticated_test_user

      response = client.get("/protected")

    assert response.status_code == 200
    assert response.data == str(authenticated_test_user).encode()
    assert get_current_user() == previous_user
  finally:
    reset_current_user(token)
