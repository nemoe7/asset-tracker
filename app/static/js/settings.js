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

const grantRolePermissionName = document.getElementById('grant-role-permission-name');
const grantRolePermissionWarning = document.getElementById('grant-role-permission-warning');

function isKnownPermission(value) {
  return KNOWN_PERMISSIONS.some(
    (permission) => permission.toLowerCase() === value.toLowerCase(),
  );
}

function syncPermissionWarning() {
  if (!grantRolePermissionWarning || !grantRolePermissionName) {
    return;
  }

  const value = grantRolePermissionName.value.trim();
  grantRolePermissionWarning.classList.toggle('hidden', !value || isKnownPermission(value));
}

grantRolePermissionName?.addEventListener('input', syncPermissionWarning);

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
const editUserRoles = document.getElementById('edit-user-roles');
const cancelEditUser = document.getElementById('cancel-edit-user');

document.querySelectorAll('.edit-user').forEach((button) => {
  button.addEventListener('click', () => {
    editUserForm.action = button.dataset.updateUrl;
    editUserUsername.value = button.dataset.userUsername ?? '';
    editUserName.value = button.dataset.userName ?? '';
    editUserPassword.value = '';

    if (editUserRoles) {
      const selected = (button.dataset.userRoles || '').split(',').filter(Boolean);
      for (const option of editUserRoles.options) {
        option.selected = selected.includes(option.value);
      }
    }

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

document.querySelectorAll('.edit-role').forEach((button) => {
  button.addEventListener('click', () => {
    editRoleForm.action = button.dataset.updateUrl;
    editRoleName.value = button.dataset.roleName ?? '';
    editRoleDescription.value = button.dataset.roleDescription ?? '';
    openModal(editRoleModal);
  });
});

cancelEditRole?.addEventListener('click', () => {
  closeModal();
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


// ==================== Manage Role Permissions ====================

const manageRolePermissionsDialog = document.getElementById('manage-role-permissions-dialog');
const manageRolePermissionsList = document.getElementById('manage-role-permissions-list');
const manageRolePermissionsStatus = document.getElementById('manage-role-permissions-status');
const cancelManageRolePermissions = document.getElementById('cancel-manage-role-permissions');
const grantRolePermissionDialog = document.getElementById('grant-role-permission-dialog');
const grantRolePermissionForm = document.getElementById('grant-role-permission-form');
const grantRolePermissionButton = document.getElementById('grant-role-permission-button');
const cancelGrantRolePermission = document.getElementById('cancel-grant-role-permission');

let currentManageRoleId = null;

document.querySelectorAll('.manage-role-permissions').forEach((button) => {
  button.addEventListener('click', () => {
    currentManageRoleId = button.dataset.roleId;
    renderManagePermissions(currentManageRoleId);
    openModal(manageRolePermissionsDialog);
  });
});

cancelManageRolePermissions?.addEventListener('click', () => {
  closeModal();
});

cancelGrantRolePermission?.addEventListener('click', () => {
  closeModal();
});

async function renderManagePermissions(roleId) {
  if (!manageRolePermissionsList) {
    return;
  }

  manageRolePermissionsList.innerHTML = '';
  manageRolePermissionsStatus?.classList.add('hidden');

  try {
    const response = await fetch(`/admin/roles/${roleId}/permissions`);

    if (!response.ok) {
      throw new Error('Failed to load permissions');
    }

    const permissions = await response.json();

    for (const permission of permissions) {
      const row = document.createElement('div');
      row.className = 'flex items-center justify-between gap-3 rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3';

      const name = document.createElement('div');
      name.className = 'min-w-0';
      name.innerHTML = `<p class="truncate text-sm font-medium text-zinc-100">${permission.name}</p>`;

      const actions = document.createElement('div');
      actions.className = 'flex shrink-0 gap-1';

      const allowedSelect = document.createElement('select');
      allowedSelect.className = 'form-input';
      allowedSelect.innerHTML = `
        <option value="1" ${permission.allowed ? 'selected' : ''}>Allowed</option>
        <option value="0" ${permission.allowed ? '' : 'selected'}>Denied</option>
      `;

      allowedSelect.addEventListener('change', async () => {
        const allowed = allowedSelect.value === '1';
        const formData = new FormData();
        formData.append('permission_name', permission.name);
        formData.append('allowed', allowed ? 'true' : 'false');
        formData.append('csrf_token', document.querySelector('input[name="csrf_token"]')?.value ?? '');

        grantRolePermissionButton?.setAttribute('disabled', '');

        try {
          const updateResponse = await fetch(`/admin/roles/${roleId}/permissions`, {
            method: 'POST',
            body: formData,
          });

          const payload = await updateResponse.json().catch(() => ({}));

          if (!updateResponse.ok) {
            showManagePermissionsError(payload.error || 'Failed to update permission.');
            return;
          }

          renderManagePermissions(roleId);
        } catch {
          showManagePermissionsError('Failed to update permission.');
        } finally {
          grantRolePermissionButton?.removeAttribute('disabled');
        }
      });

      const revokeButton = document.createElement('button');
      revokeButton.type = 'button';
      revokeButton.className = 'rounded-lg p-2 text-red-400 transition hover:bg-red-950 hover:text-red-300';
      revokeButton.title = 'Remove permission';
      revokeButton.setAttribute('aria-label', 'Remove permission');
      revokeButton.innerHTML = '<i class="bi bi-x-lg" aria-hidden="true"></i>';

      revokeButton.addEventListener('click', async () => {
        const formData = new FormData();
        formData.append('csrf_token', document.querySelector('input[name="csrf_token"]')?.value ?? '');

        try {
          const response = await fetch(`/admin/roles/${roleId}/permissions/${permission.id}/delete`, {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            showManagePermissionsError(payload.error || 'Failed to remove permission.');
            return;
          }

          renderManagePermissions(roleId);
        } catch {
          showManagePermissionsError('Failed to remove permission.');
        }
      });

      actions.appendChild(allowedSelect);
      actions.appendChild(revokeButton);
      row.appendChild(name);
      row.appendChild(actions);
      manageRolePermissionsList.appendChild(row);
    }
  } catch {
    manageRolePermissionsStatus.textContent = 'Failed to load permissions.';
    manageRolePermissionsStatus.classList.remove('hidden');
  }
}

function showManagePermissionsError(message) {
  if (!manageRolePermissionsStatus) {
    return;
  }

  manageRolePermissionsStatus.textContent = message;
  manageRolePermissionsStatus.classList.remove('hidden');
  manageRolePermissionsStatus.classList.add('text-red-400');
}

document.querySelectorAll('.grant-role-permission').forEach((button) => {
  button.addEventListener('click', () => {
    currentManageRoleId = button.dataset.roleId;
    openModal(grantRolePermissionDialog);
  });
});

grantRolePermissionForm?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData(grantRolePermissionForm);
  formData.append('csrf_token', document.querySelector('input[name="csrf_token"]')?.value ?? '');

  const status = document.getElementById('grant-role-permission-status');
  status?.classList.add('hidden');

  grantRolePermissionButton?.setAttribute('disabled', '');

  try {
    const response = await fetch(`/admin/roles/${currentManageRoleId}/permissions`, {
      method: 'POST',
      body: formData,
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      if (status) {
        status.textContent = payload.error || 'Failed to grant permission.';
        status.classList.remove('hidden');
        status.classList.add('text-red-400');
      }
      return;
    }

    grantRolePermissionForm.reset();
    grantRolePermissionWarning?.classList.add('hidden');
    closeModal();
    renderManagePermissions(currentManageRoleId);
  } catch {
    if (status) {
      status.textContent = 'Failed to grant permission.';
      status.classList.remove('hidden');
      status.classList.add('text-red-400');
    }
  } finally {
    grantRolePermissionButton?.removeAttribute('disabled');
  }
});

// ==================== End Manage Role Permissions ====================


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
