from app.services.data.setup import is_first_run


def test_is_first_run_is_cached(gen_init_db, monkeypatch):
  from app.services.data import setup as setup_module

  call_count = 0
  original_db_connection = setup_module.db_connection

  def counting_db_connection(*args, **kwargs):
    nonlocal call_count
    call_count += 1

    return original_db_connection(*args, **kwargs)

  monkeypatch.setattr(setup_module, "db_connection", counting_db_connection)

  result1 = is_first_run()
  assert call_count == 1

  result2 = is_first_run()
  assert call_count == 1
  assert result1 == result2
