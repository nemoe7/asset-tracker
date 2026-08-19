from app.db import get_db


def is_first_run():
  connection = get_db()

  try:
    result = connection.execute(
      """
      SELECT 1
      FROM users
      LIMIT 1
      """
    ).fetchone()

    return result is None
  finally:
    connection.close()
