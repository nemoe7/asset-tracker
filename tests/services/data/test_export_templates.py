import pytest

from app.services.data.export_templates import (
  create_export_template,
  delete_export_template,
  get_export_template,
  get_export_templates,
  update_export_template,
)
from app.services.exceptions.data.export_templates import (
  ExportTemplateAccessError,
  ExportTemplateNotFoundError,
  InvalidExportTemplateConfigurationError,
  InvalidExportTemplateNameError,
)

VALID_CONFIG = {
  "filters": [["3", "eq", "5"]],
  "columns": ["name", "location"],
}


@pytest.fixture
def other_user_id(gen_test_data_user):
  return gen_test_data_user("alice")


def test_create_personal_template(gen_test_data_admin):
  template_id = create_export_template(
    gen_test_data_admin,
    "My template",
    VALID_CONFIG,
  )

  template = get_export_template(template_id, gen_test_data_admin)

  assert template["name"] == "My template"
  assert template["configuration"] == VALID_CONFIG
  assert template["owner_id"] == gen_test_data_admin
  assert template["shared"] is False


def test_create_shared_template(gen_test_data_admin):
  template_id = create_export_template(
    gen_test_data_admin,
    "Shared",
    VALID_CONFIG,
    shared=True,
  )

  template = get_export_template(template_id, gen_test_data_admin)

  assert template["shared"] is True
  assert template["owner_id"] is None


def test_create_template_rejects_empty_name(gen_test_data_admin):
  with pytest.raises(InvalidExportTemplateNameError):
    create_export_template(gen_test_data_admin, "   ", VALID_CONFIG)


@pytest.mark.parametrize(
  "configuration",
  [
    [],
    "filters",
    {"unknown": 1},
    {"filters": "nope"},
    {"filters": [["3", "eq"]]},
    {"filters": [[3, "eq", "5"]]},
    {"filters": [["3", "eq", 5]]},
    {"columns": []},
    {"columns": ["name", "name"]},
    {"columns": [1]},
  ],
)
def test_create_template_rejects_invalid_configuration(
  gen_test_data_admin,
  configuration,
):
  with pytest.raises(InvalidExportTemplateConfigurationError):
    create_export_template(gen_test_data_admin, "T", configuration)


def test_create_template_allows_empty_configuration(gen_test_data_admin):
  template_id = create_export_template(gen_test_data_admin, "T", {})

  template = get_export_template(template_id, gen_test_data_admin)

  assert template["configuration"] == {}


def test_list_returns_personal_and_shared(
  gen_test_data_admin,
  other_user_id,
):
  shared_id = create_export_template(
    gen_test_data_admin,
    "Shared",
    VALID_CONFIG,
    shared=True,
  )
  personal_id = create_export_template(
    other_user_id,
    "Personal",
    VALID_CONFIG,
  )

  templates = get_export_templates(other_user_id)
  by_id = {t["id"]: t for t in templates}

  assert set(by_id) == {shared_id, personal_id}
  assert by_id[shared_id]["shared"] is True
  assert by_id[personal_id]["shared"] is False


def test_get_template_hidden_from_other_users(
  gen_test_data_admin,
  other_user_id,
):
  template_id = create_export_template(
    gen_test_data_admin,
    "Personal",
    VALID_CONFIG,
  )

  with pytest.raises(ExportTemplateNotFoundError):
    get_export_template(template_id, other_user_id)


def test_get_missing_template_raises(gen_test_data_admin):
  with pytest.raises(ExportTemplateNotFoundError):
    get_export_template(9999, gen_test_data_admin)


def test_update_template(gen_test_data_admin):
  template_id = create_export_template(gen_test_data_admin, "T", VALID_CONFIG)

  updated = update_export_template(
    template_id,
    gen_test_data_admin,
    name="Renamed",
    configuration={"columns": ["name"]},
  )

  assert updated["name"] == "Renamed"
  assert updated["configuration"] == {"columns": ["name"]}


def test_update_template_requires_changes(gen_test_data_admin):
  template_id = create_export_template(gen_test_data_admin, "T", VALID_CONFIG)

  with pytest.raises(InvalidExportTemplateConfigurationError):
    update_export_template(template_id, gen_test_data_admin)


def test_update_other_users_template_denied(
  gen_test_data_admin,
  other_user_id,
):
  template_id = create_export_template(
    gen_test_data_admin,
    "T",
    VALID_CONFIG,
  )

  with pytest.raises(ExportTemplateNotFoundError):
    update_export_template(template_id, other_user_id, name="Hacked")


def test_update_shared_template_by_non_admin_denied(
  gen_test_data_admin,
  other_user_id,
):
  template_id = create_export_template(
    gen_test_data_admin,
    "Shared",
    VALID_CONFIG,
    shared=True,
  )

  with pytest.raises(ExportTemplateAccessError):
    update_export_template(template_id, other_user_id, name="Hacked")


def test_delete_template(gen_test_data_admin):
  template_id = create_export_template(gen_test_data_admin, "T", VALID_CONFIG)

  delete_export_template(template_id, gen_test_data_admin)

  with pytest.raises(ExportTemplateNotFoundError):
    get_export_template(template_id, gen_test_data_admin)


def test_delete_other_users_template_denied(
  gen_test_data_admin,
  other_user_id,
):
  template_id = create_export_template(gen_test_data_admin, "T", VALID_CONFIG)

  with pytest.raises(ExportTemplateNotFoundError):
    delete_export_template(template_id, other_user_id)


def test_template_crud_creates_audit_logs(gen_test_data_admin):
  from app.services.data.audit import get_audit_logs

  template_id = create_export_template(gen_test_data_admin, "T", VALID_CONFIG)
  update_export_template(template_id, gen_test_data_admin, name="T2")
  delete_export_template(template_id, gen_test_data_admin)

  actions = [log["action"] for log in get_audit_logs()]

  assert "created" in actions
  assert "updated" in actions
  assert "deleted" in actions
