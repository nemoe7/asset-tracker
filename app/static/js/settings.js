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
