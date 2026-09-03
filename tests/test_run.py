from flask import Flask

import run


def test_run_module_exposes_app_for_gunicorn():
  assert isinstance(run.app, Flask)
