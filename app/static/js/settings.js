// ==================== Tabs ====================

const tabButtons = document.querySelectorAll('[data-tab-button]');
const tabPanels = document.querySelectorAll('[data-tab-panel]');

function activateTab(name) {
  for (const button of tabButtons) {
    const active = button.dataset.tabButton === name;
    button.classList.toggle('bg-zinc-800', active);
    button.classList.toggle('text-zinc-100', active);
  }

  for (const panel of tabPanels) {
    panel.classList.toggle('hidden', panel.dataset.tabPanel !== name);
  }
}

for (const button of tabButtons) {
  button.addEventListener('click', () => {
    activateTab(button.dataset.tabButton);

    // Rewrite only the tab param so a reload lands on the same tab;
    // replaceState never pushes a history entry.
    const url = new URL(window.location.href);
    url.searchParams.set('tab', button.dataset.tabButton);
    history.replaceState(null, '', url);
  });
}

const initialTab =
  [...tabPanels].find((panel) => !panel.classList.contains('hidden'))
    ?.dataset.tabPanel ?? tabButtons[0]?.dataset.tabButton;

if (initialTab) {
  activateTab(initialTab);
}

// ==================== Add Location Modal ====================

const addLocationModal = document.getElementById('add-location-dialog');
const addLocationButton = document.getElementById('add-location-button');
const cancelAddLocation = document.getElementById('cancel-add-location');

addLocationButton?.addEventListener('click', () => {
  openModal(addLocationModal);
});

cancelAddLocation?.addEventListener('click', () => {
  closeModal();
});

// ==================== Edit Location Modal ====================

const editLocationModal = document.getElementById('edit-location-dialog');
const editLocationForm = editLocationModal?.querySelector('form');
const editLocationName = document.getElementById('edit-location-name');
const editLocationDescription = document.getElementById('edit-location-description');
const cancelEditLocation = document.getElementById('cancel-edit-location');

document.querySelectorAll('.edit-location').forEach((button) => {
  button.addEventListener('click', () => {
    editLocationForm.action = button.dataset.updateUrl;
    editLocationName.value = button.dataset.locationName ?? '';
    editLocationDescription.value = button.dataset.locationDescription ?? '';
    openModal(editLocationModal);
  });
});

cancelEditLocation?.addEventListener('click', () => {
  closeModal();
});

// ==================== Delete Location Confirmation ====================

const deleteLocationModal = document.getElementById('delete-location-dialog');
const cancelDeleteLocation = document.getElementById('cancel-delete-location');
const confirmDeleteLocation = document.getElementById('confirm-delete-location');

let pendingDeleteLocationForm = null;

document.querySelectorAll('[data-delete-location]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (form.dataset.confirmed === 'true') {
      return;
    }

    event.preventDefault();
    pendingDeleteLocationForm = form;
    openModal(deleteLocationModal);
  });
});

cancelDeleteLocation?.addEventListener('click', () => {
  pendingDeleteLocationForm = null;
  closeModal();
});

confirmDeleteLocation?.addEventListener('click', () => {
  closeModal();

  if (pendingDeleteLocationForm) {
    pendingDeleteLocationForm.dataset.confirmed = 'true';
    pendingDeleteLocationForm.submit();
    pendingDeleteLocationForm = null;
  }
});

// ==================== Add Custom Field Modal ====================

const addFieldModal = document.getElementById('add-field-dialog');

for (const button of document.querySelectorAll('#add-field-button, #empty-add-field-button')) {
  button?.addEventListener('click', () => {
    openModal(addFieldModal);
  });
}

document.getElementById('cancel-add-field')?.addEventListener('click', () => {
  closeModal();
});

// ==================== Edit Custom Field Modal ====================

const editFieldModal = document.getElementById('edit-field-dialog');
const editFieldForm = editFieldModal?.querySelector('form');
const editFieldName = document.getElementById('edit-field-name');
const editFieldType = document.getElementById('edit-field-type');
const editFieldDescription = document.getElementById('edit-field-description');
const editFieldRequired = document.getElementById('edit-field-required');
const editFieldEnumValues = document.getElementById('edit-field-enum-values');

document.querySelectorAll('.edit-field').forEach((button) => {
  button.addEventListener('click', () => {
    editFieldForm.action = button.dataset.updateUrl;
    editFieldName.value = button.dataset.fieldName ?? '';
    editFieldType.value = button.dataset.fieldType ?? 'text';
    editFieldDescription.value = button.dataset.fieldDescription ?? '';
    editFieldRequired.checked = button.dataset.fieldRequired === 'true';
    editFieldEnumValues.value = button.dataset.fieldEnumValues ?? '';

    syncEnumValues();
    openModal(editFieldModal);
  });
});

document.getElementById('cancel-edit-field')?.addEventListener('click', () => {
  closeModal();
});

// ==================== Field Permissions Modal ====================

const fieldPermissionsDialog = document.getElementById('field-permissions-dialog');
const fieldPermissionsBody = document.getElementById('field-permissions-body');
const cancelFieldPermissions = document.getElementById('cancel-field-permissions');
const saveFieldPermissions = document.getElementById('save-field-permissions');

let currentFieldPermissions = null;

function renderFieldPermissions() {
  if (!fieldPermissionsBody) return;

  fieldPermissionsBody.innerHTML = '';

  const table = document.createElement('div');
  table.className = 'divide-y divide-zinc-800 rounded-lg border border-zinc-800';

  for (const role of currentFieldPermissions.roles) {
    const row = document.createElement('div');
    row.className = 'flex items-center justify-between gap-3 px-4 py-3';

    const name = document.createElement('span');
    name.className = 'text-sm font-medium text-zinc-200';
    name.textContent = role.name;
    row.append(name);

    const toggles = document.createElement('div');
    toggles.className = 'flex items-center gap-5';

    for (const op of ['read', 'update']) {
      const label = document.createElement('label');
      label.className = 'flex items-center gap-2 text-sm text-zinc-300';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'size-4 rounded border-zinc-600 bg-zinc-900 text-zinc-100 focus:ring-zinc-500';
      checkbox.dataset.roleId = String(role.id);
      checkbox.dataset.op = op;
      checkbox.checked = role[op];

      label.append(checkbox, document.createTextNode(op === 'read' ? 'View' : 'Edit'));
      toggles.append(label);
    }

    row.append(toggles);
    table.append(row);
  }

  fieldPermissionsBody.append(table);
}

async function openFieldPermissions(fieldId) {
  if (!fieldPermissionsBody) return;

  fieldPermissionsBody.innerHTML = '<p class="text-sm text-zinc-500">Loading…</p>';

  try {
    const response = await fetch(`/admin/custom-fields/${fieldId}/permissions`);
    if (!response.ok) throw new Error('Failed to load permissions');

    const payload = await response.json();

    currentFieldPermissions = {
      fieldId,
      roles: payload.roles.map((role) => ({
        ...role,
        read: !!payload.permissions[role.id]?.read,
        update: !!payload.permissions[role.id]?.update,
      })),
    };

    renderFieldPermissions();
    openModal(fieldPermissionsDialog);
  } catch {
    fieldPermissionsBody.innerHTML = '<p class="text-sm text-red-400">Failed to load permissions.</p>';
  }
}

document.querySelectorAll('.field-permissions').forEach((button) => {
  button.addEventListener('click', () => {
    openFieldPermissions(button.dataset.fieldId);
  });
});

cancelFieldPermissions?.addEventListener('click', () => {
  closeModal();
});

saveFieldPermissions?.addEventListener('click', async () => {
  if (!currentFieldPermissions) return;

  const readRoleIds = [];
  const updateRoleIds = [];

  fieldPermissionsBody.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    if (!checkbox.checked) return;
    (checkbox.dataset.op === 'read' ? readRoleIds : updateRoleIds).push(checkbox.dataset.roleId);
  });

  const body = new FormData();
  body.append('csrf_token', document.querySelector('input[name="csrf_token"]')?.value ?? '');
  for (const id of readRoleIds) body.append('read_role_ids', id);
  for (const id of updateRoleIds) body.append('update_role_ids', id);

  const response = await fetch(
    `/admin/custom-fields/${currentFieldPermissions.fieldId}/permissions`,
    { method: 'POST', body },
  );

  if (!response.ok) {
    fieldPermissionsBody.innerHTML = '<p class="text-sm text-red-400">Failed to save permissions.</p>';
    return;
  }

  closeModal();
});

// ==================== End Field Permissions Modal ====================

// ==================== Archive Custom Field Confirmation ====================

const archiveFieldModal = document.getElementById('archive-field-dialog');
const cancelArchiveField = document.getElementById('cancel-archive-field');
const confirmArchiveField = document.getElementById('confirm-archive-field');

let pendingArchiveFieldForm = null;

document.querySelectorAll('[data-archive-field]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (form.dataset.confirmed === 'true') {
      return;
    }

    event.preventDefault();
    pendingArchiveFieldForm = form;
    openModal(archiveFieldModal);
  });
});

cancelArchiveField?.addEventListener('click', () => {
  pendingArchiveFieldForm = null;
  closeModal();
});

confirmArchiveField?.addEventListener('click', () => {
  closeModal();

  if (pendingArchiveFieldForm) {
    pendingArchiveFieldForm.dataset.confirmed = 'true';
    pendingArchiveFieldForm.submit();
    pendingArchiveFieldForm = null;
  }
});

// ==================== Enum Values Toggle ====================

function syncEnumValues() {
  for (const container of document.querySelectorAll('[data-enum-values]')) {
    const select = container.closest('form')?.querySelector('[data-enum-toggle]');
    const visible = select?.value === 'enum';
    container.classList.toggle('hidden', !visible);
  }
}

document.querySelectorAll('[data-enum-toggle]').forEach((select) => {
  select.addEventListener('change', syncEnumValues);
});

syncEnumValues();

// ==================== Known Permissions ====================

const KNOWN_PERMISSIONS = [
  "locations.manage",
  "custom_fields.manage",
  "users.manage",
  "roles.manage",
  "audit.read",
  "backups.create",
  "backups.restore",
];

const knownPermissionsList = document.getElementById('known-permissions-list');

if (knownPermissionsList) {
  for (const permission of KNOWN_PERMISSIONS) {
    const option = document.createElement('option');
    option.value = permission;
    knownPermissionsList.appendChild(option);
  }
}

// ==================== End Known Permissions ====================


// ==================== Add User Modal ====================

const addUserModal = document.getElementById('add-user-dialog');
const addUserButton = document.getElementById('add-user-button');
const cancelAddUser = document.getElementById('cancel-add-user');

for (const button of [addUserButton, document.getElementById('empty-add-user-button')]) {
  button?.addEventListener('click', () => {
    openModal(addUserModal);
  });
}

cancelAddUser?.addEventListener('click', () => {
  closeModal();
});

// ==================== End Add User Modal ====================


// ==================== Edit User Modal ====================

const editUserModal = document.getElementById('edit-user-dialog');
const editUserForm = editUserModal?.querySelector('form');
const editUserUsername = document.getElementById('edit-user-username');
const editUserName = document.getElementById('edit-user-name');
const editUserPassword = document.getElementById('edit-user-password');
const cancelEditUser = document.getElementById('cancel-edit-user');

// Chip-based roles, mirroring the export-column add flow.
const editUserRolesList = document.getElementById('edit-user-roles-list');
const editUserRolesInput = document.getElementById('edit-user-roles-input');
const editUserRolesAdd = document.getElementById('edit-user-roles-add');
const editUserRolesOptions = document.getElementById('edit-user-roles-options');
const editUserRolesError = document.getElementById('edit-user-roles-error');
const editUserRolesValues = document.getElementById('edit-user-roles-values');
const editUserRolesData = document.getElementById('edit-user-roles-data');

// Assignable roles resolved from the page data: by id and by lowercased name.
let editUserRolesById = {};
let editUserRolesByName = {};

if (editUserRolesData) {
  try {
    const roles = JSON.parse(editUserRolesData.textContent.trim() || '[]');
    for (const role of roles) {
      editUserRolesById[String(role.id)] = role;
      editUserRolesByName[role.name.toLowerCase()] = role;
    }
  } catch {
    editUserRolesById = {};
    editUserRolesByName = {};
  }
}

function buildEditUserRoleRow(role) {
  const row = document.createElement('div');
  row.className = 'edit-user-role-row flex w-fit max-w-full items-center gap-1.5 rounded-full border border-zinc-700 py-1 pl-3 pr-1.5';
  row.dataset.roleId = String(role.id);

  const label = document.createElement('span');
  label.className = 'edit-user-role-name min-w-0 truncate text-sm text-zinc-200';
  label.textContent = role.name;

  const removeButton = document.createElement('button');
  removeButton.type = 'button';
  removeButton.className = 'edit-user-role-remove flex size-5 shrink-0 items-center justify-center rounded-full text-red-400 hover:bg-red-950 hover:text-red-300';
  removeButton.title = 'Remove role';
  removeButton.setAttribute('aria-label', 'Remove role');
  removeButton.innerHTML = '<i class="bi bi-x-lg block" aria-hidden="true"></i>';
  removeButton.addEventListener('click', () => {
    row.remove();
    syncEditUserRoleInputs();
    refreshEditUserRoleOptions();
  });

  row.append(label, removeButton);
  return row;
}

function setEditUserRoles(roles) {
  editUserRolesList?.replaceChildren(...roles.map(buildEditUserRoleRow));
  syncEditUserRoleInputs();
  refreshEditUserRoleOptions();
}

// Rebuild the datalist from all assignable roles minus the ones already added.
function refreshEditUserRoleOptions() {
  if (!editUserRolesOptions) return;

  const selected = new Set(
    [...editUserRolesList.querySelectorAll('.edit-user-role-row')].map(
      (row) => row.dataset.roleId
    )
  );

  editUserRolesOptions.replaceChildren(
  ...Object.values(editUserRolesById)
    .filter((role) => !selected.has(String(role.id)))
    .map((role) => new Option(role.name, role.name))
  );
}

// Keep the hidden role_ids inputs in sync with the rendered chips so the form
// still submits role_ids as a list, matching the backend's getlist contract.
function syncEditUserRoleInputs() {
  if (!editUserRolesValues) return;

  editUserRolesValues.replaceChildren(
    ...[...editUserRolesList.querySelectorAll('.edit-user-role-row')].map((row) => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'role_ids';
      input.value = row.dataset.roleId;
      return input;
    })
  );
}

function addEditUserRoleByName(rawName) {
  const name = rawName.trim();
  if (!name) return;

  const role = editUserRolesByName[name.toLowerCase()];
  const existing = [...editUserRolesList.querySelectorAll('.edit-user-role-row')]
    .some((row) => row.dataset.roleId === String(role?.id));

  const valid = role !== undefined && !existing;
  editUserRolesError?.classList.toggle('hidden', valid);

  if (!valid) return;

  editUserRolesList?.append(buildEditUserRoleRow(role));
  syncEditUserRoleInputs();
  refreshEditUserRoleOptions();
  if (editUserRolesInput) editUserRolesInput.value = '';
}

function submitEditUserRole() {
  addEditUserRoleByName(editUserRolesInput.value);
}

// Hide the error while typing a new value.
editUserRolesInput?.addEventListener('input', () => {
  editUserRolesError?.classList.add('hidden');
});

// Add a role when Enter is pressed instead of submitting the form.
editUserRolesInput?.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter') return;
  event.preventDefault();
  submitEditUserRole();
});

// Add a role via the explicit Add button.
editUserRolesAdd?.addEventListener('click', submitEditUserRole);

document.querySelectorAll('.edit-user').forEach((button) => {
  button.addEventListener('click', () => {
    editUserForm.action = button.dataset.updateUrl;
    editUserUsername.value = button.dataset.userUsername ?? '';
    editUserName.value = button.dataset.userName ?? '';
    editUserPassword.value = '';

    const roleIdList = (button.dataset.userRoles || '').split(',').filter(Boolean);
    const selectedRoles = roleIdList
      .map((id) => editUserRolesById[id])
      .filter(Boolean);
    setEditUserRoles(selectedRoles);

    openModal(editUserModal);
  });
});

cancelEditUser?.addEventListener('click', () => {
  closeModal();
});

// ==================== End Edit User Modal ====================


// ==================== Archive User Confirmation ====================

const archiveUserModal = document.getElementById('archive-user-dialog');
const cancelArchiveUser = document.getElementById('cancel-archive-user');
const confirmArchiveUser = document.getElementById('confirm-archive-user');

let pendingArchiveUserForm = null;

document.querySelectorAll('[data-archive-user]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (form.dataset.confirmed === 'true') {
      return;
    }

    event.preventDefault();
    pendingArchiveUserForm = form;
    openModal(archiveUserModal);
  });
});

cancelArchiveUser?.addEventListener('click', () => {
  pendingArchiveUserForm = null;
  closeModal();
});

confirmArchiveUser?.addEventListener('click', () => {
  closeModal();

  if (pendingArchiveUserForm) {
    pendingArchiveUserForm.dataset.confirmed = 'true';
    pendingArchiveUserForm.submit();
    pendingArchiveUserForm = null;
  }
});

// ==================== End Archive User Confirmation ====================


// ==================== Add Role Modal ====================

const addRoleModal = document.getElementById('add-role-dialog');
const addRoleButton = document.getElementById('add-role-button');
const cancelAddRole = document.getElementById('cancel-add-role');

addRoleButton?.addEventListener('click', () => {
  openModal(addRoleModal);
});

for (const button of [addRoleButton, document.getElementById('empty-add-role-button')]) {
  button?.addEventListener('click', () => {
    openModal(addRoleModal);
  });
}

cancelAddRole?.addEventListener('click', () => {
  closeModal();
});

// ==================== End Add Role Modal ====================


// ==================== Edit Role Modal ====================

const editRoleModal = document.getElementById('edit-role-dialog');
const editRoleForm = editRoleModal?.querySelector('form');
const editRoleName = document.getElementById('edit-role-name');
const editRoleDescription = document.getElementById('edit-role-description');
const cancelEditRole = document.getElementById('cancel-edit-role');

cancelEditRole?.addEventListener('click', () => {
  closeModal();
});

const editRolePermissionsList = document.getElementById('edit-role-permissions-list');
const editRolePermissionName = document.getElementById('edit-role-permission-name');
const editRolePermissionAdd = document.getElementById('edit-role-permission-add');
const editRolePermissionError = document.getElementById('edit-role-permission-error');
let currentEditRoleId = null;
let originalPermissions = [];
let stagedPermissions = [];

// Keep the known-permissions autocomplete in sync with staged permissions so
// permissions already added (or already present on load) are not offered again.
function refreshKnownPermissionOptions() {
  if (!knownPermissionsList) return;
  const staged = new Set(stagedPermissions.map((p) => p.permission.toLowerCase()));
  knownPermissionsList.replaceChildren(
    ...KNOWN_PERMISSIONS.filter((p) => !staged.has(p.toLowerCase())).map(
      (p) => new Option(p, p)
    )
  );
}

function renderStagedPermissions() {
  if (!editRolePermissionsList) return;
  editRolePermissionsList.innerHTML = '';

  for (const permission of stagedPermissions) {
    // Chip-style permission, mirroring the edit-user roles flow. Clicking the
    // chip toggles between allowed/denied instead of using a dropdown.
    const wrapper = document.createElement('div');
    wrapper.className = `edit-role-permission-chip flex w-fit max-w-full items-center gap-1.5 rounded-full border py-1 pl-1.5 pr-1.5 ${
      permission.allowed
        ? 'border-emerald-900 bg-emerald-900 text-emerald-100'
        : 'border-red-900 bg-red-900 text-red-100'
    }`;

    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'flex min-w-0 items-center gap-1.5 pl-1.5';
    chip.title = permission.allowed ? 'Allowed - click to deny' : 'Denied - click to allow';
    chip.setAttribute('aria-pressed', String(permission.allowed));
    chip.addEventListener('click', () => {
      permission.allowed = !permission.allowed;
      renderStagedPermissions();
    });

    const label = document.createElement('span');
    label.className = 'edit-role-permission-name min-w-0 truncate text-sm font-medium';
    label.textContent = permission.permission;

    chip.append(label);

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'flex size-5 shrink-0 items-center justify-center rounded-full text-red-400 hover:bg-red-950 hover:text-red-300';
    removeButton.title = 'Remove permission';
    removeButton.setAttribute('aria-label', 'Remove permission');
    removeButton.innerHTML = '<i class="bi bi-x-lg block" aria-hidden="true"></i>';
    removeButton.addEventListener('click', () => {
      stagedPermissions = stagedPermissions.filter((p) => p !== permission);
      renderStagedPermissions();
    });

    wrapper.append(chip, removeButton);
    editRolePermissionsList.appendChild(wrapper);
  }

  refreshKnownPermissionOptions();
}

async function renderEditRolePermissions(roleId) {
  if (!editRolePermissionsList) return;
  currentEditRoleId = roleId;
  editRolePermissionError?.classList.add('hidden');

  try {
    const response = await fetch(`/admin/roles/${roleId}/permissions`);
    if (!response.ok) throw new Error('Failed to load permissions');
    const permissions = await response.json();

    originalPermissions = permissions.map((p) => ({
      permission_id: p.permission_id,
      permission: p.permission,
      allowed: !!p.allowed,
    }));
    stagedPermissions = originalPermissions.map((p) => ({ ...p, isNew: false }));
    renderStagedPermissions();
  } catch {
    editRolePermissionsList.innerHTML = '<p class="text-sm text-red-400">Failed to load permissions.</p>';
  }
}

function showEditRolePermissionError(message) {
  if (!editRolePermissionError) return;
  editRolePermissionError.textContent = message;
  editRolePermissionError.classList.remove('hidden');
  editRolePermissionError.classList.add('text-red-400');
}

document.querySelectorAll('.edit-role').forEach((button) => {
  button.addEventListener('click', () => {
    editRoleForm.action = button.dataset.updateUrl;
    editRoleName.value = button.dataset.roleName ?? '';
    editRoleDescription.value = button.dataset.roleDescription ?? '';
    editRolePermissionError?.classList.add('hidden');
    openModal(editRoleModal);
    renderEditRolePermissions(button.dataset.roleId);
  });
});

function addEditRolePermission() {
  if (!currentEditRoleId || !editRolePermissionName) return;

  const permissionName = editRolePermissionName.value.trim();
  if (!permissionName) return;

  const duplicate = stagedPermissions.some(
  (p) => p.permission.toLowerCase() === permissionName.toLowerCase()
  );
  editRolePermissionError?.classList.toggle('hidden', !duplicate);

  if (duplicate) return;

  stagedPermissions.push({ permission: permissionName, allowed: true, isNew: true });

  editRolePermissionName.value = '';
  editRolePermissionName.focus();
  renderStagedPermissions();
}

function submitEditRolePermission() {
  addEditRolePermission();
}

// Hide the error while typing a new value.
editRolePermissionName?.addEventListener('input', () => {
  editRolePermissionError?.classList.add('hidden');
});

// Add a permission when Enter is pressed instead of submitting the form.
editRolePermissionName?.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter') return;
  event.preventDefault();
  submitEditRolePermission();
});

// Add a permission via the explicit Add button.
editRolePermissionAdd?.addEventListener('click', submitEditRolePermission);

// Persist staged permission changes only on explicit save. A fetched response
// that followed a 302 is a success; a validation error renders the page (200).
async function persistPermissionChanges() {
  const csrf = editRoleForm?.querySelector('input[name="csrf_token"]')?.value ?? '';
  const originalByName = new Map(originalPermissions.map((p) => [p.permission, p]));

  // Deletes: permissions that existed on load but were removed from the staging list.
  for (const original of originalPermissions) {
    if (!stagedPermissions.some((p) => p.permission === original.permission)) {
      const body = new FormData();
      body.append('csrf_token', csrf);
      const res = await fetch(
        `/admin/roles/${currentEditRoleId}/permissions/${original.permission_id}/delete`,
        { method: 'POST', body },
      );
      if (!res.redirected) {
        showEditRolePermissionError('Failed to remove a permission.');
        return false;
      }
    }
  }

  // Sets: newly added permissions or allow/deny toggles.
  for (const staged of stagedPermissions) {
    const original = originalByName.get(staged.permission);
    if (staged.isNew || !original || original.allowed !== staged.allowed) {
      const body = new FormData();
      body.append('csrf_token', csrf);
      body.append('permission_name', staged.permission);
      body.append('allowed', staged.allowed ? 'true' : 'false');
      const res = await fetch(`/admin/roles/${currentEditRoleId}/permissions`, {
        method: 'POST',
        body,
      });
      if (!res.redirected) {
        showEditRolePermissionError('Failed to save a permission.');
        return false;
      }
    }
  }

  return true;
}

editRoleForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const persisted = await persistPermissionChanges();
  if (!persisted) return;
  // The native submit still handles the role name/description update and its
  // validation + redirect; submit() bypasses this submit listener.
  editRoleForm.submit();
});

// ==================== End Edit Role Modal ====================


// ==================== Delete Role Confirmation ====================

const deleteRoleModal = document.getElementById('delete-role-dialog');
const cancelDeleteRole = document.getElementById('cancel-delete-role');
const confirmDeleteRole = document.getElementById('confirm-delete-role');

let pendingDeleteRoleForm = null;

document.querySelectorAll('[data-delete-role]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (form.dataset.confirmed === 'true') {
      return;
    }

    event.preventDefault();
    pendingDeleteRoleForm = form;
    openModal(deleteRoleModal);
  });
});

cancelDeleteRole?.addEventListener('click', () => {
  pendingDeleteRoleForm = null;
  closeModal();
});

confirmDeleteRole?.addEventListener('click', () => {
  closeModal();

  if (pendingDeleteRoleForm) {
    pendingDeleteRoleForm.dataset.confirmed = 'true';
    pendingDeleteRoleForm.submit();
    pendingDeleteRoleForm = null;
  }
});

// ==================== End Delete Role Confirmation ====================


// ==================== Manual Backup ====================

const backupButton = document.getElementById('backup-button');
const backupStatus = document.getElementById('backup-status');

function showBackupStatus(message, isError) {
  if (!backupStatus) {
    return;
  }

  backupStatus.textContent = message;
  backupStatus.classList.remove('hidden');
  backupStatus.classList.toggle('text-red-400', isError);
  backupStatus.classList.toggle('text-emerald-400', !isError);
}

backupButton?.addEventListener('click', async () => {
  backupButton.setAttribute('disabled', '');
  backupStatus?.classList.add('hidden');

  try {
    const response = await fetch('/backups/create', {
      method: 'POST',
      headers: { 'X-CSRF-Token': document.querySelector('input[name="csrf_token"]')?.value ?? '' }
    });

    if (!response.ok) {
      showBackupStatus('Backup failed. No backup was created.', true);
      return;
    }

    const blob = await response.blob();

    const disposition = response.headers.get('Content-Disposition') || '';

    const match = disposition.match(/filename="([^"]+)"/);

    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');

    link.href = url;
    link.download = match ? match[1] : 'backup.db';
    link.click();

    URL.revokeObjectURL(url);

    showBackupStatus('Backup downloaded successfully.', false);
  } catch {
    showBackupStatus('Backup failed. No backup was created.', true);
  } finally {
    backupButton.removeAttribute('disabled');
  }
});

// ==================== End Manual Backup ====================

// ==================== Restore From Backup ====================

const restoreForm = document.getElementById('restore-form');
const restoreFile = document.getElementById('restore-file');
const restoreStatus = document.getElementById('restore-status');
const restoreChooseButton = document.getElementById('restore-choose-button');
const restoreChooseLabel = document.getElementById('restore-choose-label');
const restoreConfirmDialog = document.getElementById('restore-confirm-dialog');
const restoreConfirmForm = document.getElementById('restore-confirm-form');
const restoreConfirmPassword = document.getElementById('restore-confirm-password');
const restoreConfirmStatus = document.getElementById('restore-confirm-status');
const restoreConfirmButton = document.getElementById('restore-confirm-button');
const cancelRestoreConfirm = document.getElementById('cancel-restore-confirm');

const restoreChooseDefault = 'Choose backup file…';

// The native file box is visually hidden; this button opens it and shows
// the chosen file's name in place of the browser's "No file chosen" text.
restoreChooseButton?.addEventListener('click', () => {
  restoreFile?.click();
});

restoreFile?.addEventListener('change', () => {
  if (restoreChooseLabel) {
    restoreChooseLabel.textContent = restoreFile?.files?.[0]?.name ?? restoreChooseDefault;
  }
});

function showRestoreStatus(message, isError) {
  if (!restoreStatus) {
    return;
  }

  restoreStatus.textContent = message;
  restoreStatus.classList.remove('hidden');
  restoreStatus.classList.toggle('text-red-400', isError);
  restoreStatus.classList.toggle('text-emerald-400', !isError);
}

function showRestoreConfirmError(message) {
  if (!restoreConfirmStatus) {
    return;
  }

  restoreConfirmStatus.textContent = message;
  restoreConfirmStatus.classList.remove('hidden');
  restoreConfirmStatus.classList.add('text-red-400');
}

// Choosing a file opens the password confirmation modal.

restoreForm?.addEventListener('submit', (event) => {
  event.preventDefault();

  if (!restoreFile?.files?.length) {
    showRestoreStatus('Choose a backup .db file to restore.', true);
    return;
  }

  if (restoreConfirmPassword) {
    restoreConfirmPassword.value = '';
  }

  restoreConfirmStatus?.classList.add('hidden');

  openModal(restoreConfirmDialog);
});

cancelRestoreConfirm?.addEventListener('click', () => {
  closeModal();
});

restoreConfirmForm?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData();

  formData.append('file', restoreFile.files[0]);
  formData.append('password', restoreConfirmPassword?.value ?? '');
  formData.append('csrf_token', document.querySelector('input[name="csrf_token"]')?.value ?? '');

  restoreConfirmButton?.setAttribute('disabled', '');
  restoreConfirmStatus?.classList.add('hidden');

  try {
    const response = await fetch('/backups/restore', {
      method: 'POST',
      body: formData,
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      showRestoreConfirmError(payload.error || 'Restore failed.');
      return;
    }

    closeModal();

    // The database was replaced; the current session is no longer valid.
    window.location.assign('/auth/login');
  } catch {
    showRestoreConfirmError('Restore failed.');
  } finally {
    restoreConfirmButton?.removeAttribute('disabled');
  }
});

// ==================== End Restore From Backup ====================

// ==================== Reset Database ====================

const resetDatabaseButton = document.getElementById('reset-database-button');
const resetDatabaseDialog = document.getElementById('reset-database-dialog');
const resetDatabaseForm = document.getElementById('reset-database-form');
const resetPassword = document.getElementById('reset-password');
const resetConfirmPassword = document.getElementById('reset-confirm-password');
const resetConfirmStatus = document.getElementById('reset-confirm-status');
const resetConfirmButton = document.getElementById('confirm-reset-database');
const cancelResetDatabase = document.getElementById('cancel-reset-database');

function showResetStatus(message, isError) {
  if (!resetConfirmStatus) {
    return;
  }

  resetConfirmStatus.textContent = message;
  resetConfirmStatus.classList.remove('hidden');
  resetConfirmStatus.classList.toggle('text-red-400', isError);
  resetConfirmStatus.classList.toggle('text-emerald-400', !isError);
}

resetDatabaseButton?.addEventListener('click', () => {
  if (resetPassword) {
    resetPassword.value = '';
  }

  if (resetConfirmPassword) {
    resetConfirmPassword.value = '';
  }

  resetConfirmStatus?.classList.add('hidden');
  openModal(resetDatabaseDialog);
});

cancelResetDatabase?.addEventListener('click', () => {
  closeModal();
});

resetDatabaseForm?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const password = resetPassword?.value ?? '';
  const confirmPassword = resetConfirmPassword?.value ?? '';

  if (password !== confirmPassword) {
    showResetStatus('Passwords do not match.', true);
    return;
  }

  const formData = new FormData();

  formData.append('password', password);
  formData.append('confirm_password', confirmPassword);
  formData.append('csrf_token', document.querySelector('input[name="csrf_token"]')?.value ?? '');

  resetConfirmButton?.setAttribute('disabled', '');
  resetConfirmStatus?.classList.add('hidden');

  try {
    const response = await fetch('/admin/data/reset', {
      method: 'POST',
      body: formData,
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      showResetStatus(payload.error || 'Reset failed.', true);
      return;
    }

    closeModal();
    window.location.assign('/auth/login');
  } catch {
    showResetStatus('Reset failed.', true);
  } finally {
    resetConfirmButton?.removeAttribute('disabled');
  }
});

// ==================== End Reset Database ====================
