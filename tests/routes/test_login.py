def test_admin_can_login(gen_test_admin, gen_test_client, gen_password):
  response = gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_password("test_admin"),
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/")


def test_admin_login_sets_session(
  gen_test_admin,
  gen_test_client,
  gen_password,
):
  gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_password("test_admin"),
    },
  )

  with gen_test_client.session_transaction() as session:
    assert session["user_id"] == gen_test_admin
    assert session.permanent is True


def test_login_is_rate_limited_after_repeated_failures(
  gen_test_admin,
  gen_test_client,
  gen_password,
):
  for _ in range(5):
    response = gen_test_client.post(
      "/auth/login",
      data={
        "username": "test_admin",
        "password": "wrong_password",
      },
    )

    assert response.status_code == 200

  response = gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_password("test_admin"),
    },
  )

  assert response.status_code == 429
  assert b"Too many failed login attempts" in response.data


def test_successful_login_clears_rate_limit_history(
  gen_test_admin,
  gen_test_client,
  gen_password,
):
  for _ in range(4):
    gen_test_client.post(
      "/auth/login",
      data={
        "username": "test_admin",
        "password": "wrong_password",
      },
    )

  gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_password("test_admin"),
    },
  )

  gen_test_client.post("/auth/logout")

  response = gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_password("test_admin"),
    },
  )

  assert response.status_code == 302


def test_admin_login_rejects_invalid_password(
  gen_test_admin,
  gen_test_client,
  gen_password,
):
  response = gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": "wrong_password",
    },
  )

  assert response.status_code == 200
  assert b"Invalid username or password." in response.data


def test_unauthenticated_user_is_redirected_to_login(
  gen_test_admin,
  gen_test_client,
):
  response = gen_test_client.get("/")

  assert response.status_code == 302
  assert response.location.endswith("/auth/login")
