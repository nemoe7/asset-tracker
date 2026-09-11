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
