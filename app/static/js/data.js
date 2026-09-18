// ==================== Import ====================

const importItemModal = document.getElementById('import-item-modal');
const importForm = document.getElementById('import-form');
const importFile = document.getElementById('import-file');
const importError = document.getElementById('import-error');
const importStatus = document.getElementById('import-status');
const importSubmitButton = document.getElementById('import-submit-button');

function showImportError(message) {
  if (!importError) {
    return;
  }

  importError.textContent = message;
  importError.classList.remove('hidden');
}

function showImportStatus(message, isError) {
  if (!importStatus) {
    return;
  }

  importStatus.textContent = message;
  importStatus.classList.remove('hidden');
  importStatus.classList.toggle('text-red-400', isError);
  importStatus.classList.toggle('text-emerald-400', !isError);
}

document
  .getElementById('import-button')
  ?.addEventListener('click', () => {
    if (importForm) {
      importForm.reset();
    }

    importError?.classList.add('hidden');
    importStatus?.classList.add('hidden');
    importFile?.classList.remove('opacity-50');

    openModal(importItemModal);
  });

importForm?.addEventListener('submit', async (event) => {
  event.preventDefault();

  if (!importFile?.files?.length) {
    showImportError('Choose a CSV or .xlsx file to import.');
    return;
  }

  const formData = new FormData(importForm);

  importSubmitButton?.setAttribute('disabled', '');
  importFile.classList.add('opacity-50');
  importError?.classList.add('hidden');

  try {
    const response = await fetch('/inventory/import', {
      method: 'POST',
      body: formData,
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      showImportError(payload.error || 'Import failed.');
      return;
    }

    closeModal();

    const importedCount = payload.imported_count ?? 0;

    showImportStatus(
      `Imported ${importedCount} asset${importedCount === 1 ? '' : 's'}.`,
      false
    );
  } catch {
    showImportError('Import failed.');
  } finally {
    importSubmitButton?.removeAttribute('disabled');
    importFile.classList.remove('opacity-50');
  }
});

// ==================== End Import ====================


// ==================== Export Modal ====================

// Keep in sync with _BUILTIN_COLUMNS in app/services/export.py.
const BUILTIN_EXPORT_FIELDS = [
  ['id', 'ID'],
  ['name', 'Name'],
  ['description', 'Description'],
  ['location', 'Location'],
  ['created_at', 'Created at'],
  ['updated_at', 'Updated at'],
  ['archival_reason', 'Archival reason'],
  ['archival_notes', 'Archival notes']
];

const exportItemModal = document.getElementById('export-item-modal');
const exportForm = document.getElementById('export-form');
const exportColumnRows = document.getElementById('export-column-rows');
const exportColumnOptions = document.getElementById(
  'export-column-options'
);
const addExportColumn = document.getElementById('add-export-column');
const addExportColumnError = document.getElementById(
  'add-export-column-error'
);
const exportColumnsReset = document.getElementById('export-columns-reset');
const addExportColumnButton = document.getElementById(
  'add-export-column-button'
);

async function loadCustomFields() {
  try {
    const response = await fetch('/custom-fields');

    return response.ok ? await response.json() : [];
  } catch (error) {
    console.error('Failed to load custom fields:', error);
    return [];
  }
}

// Full list of available column names; the datalist excludes the columns
// that are already selected.
let exportColumnChoices = [];

function buildExportColumnRow(name) {
  // Pill-style row: short names share a line and wrap naturally; a name
  // wider than the container gets its own row (max-w-full) with the label
  // truncated instead of overflowing.
  const row = document.createElement('div');

  row.className =
    'export-column-row flex w-fit max-w-full items-center gap-1.5 rounded-full border border-zinc-700 py-1 pl-3 pr-1.5';

  const label = document.createElement('span');

  label.className = 'export-column-name min-w-0 truncate text-sm text-zinc-200';
  label.textContent = name;

  const removeButton = document.createElement('button');

  removeButton.type = 'button';
  removeButton.className =
    'export-column-remove flex size-5 shrink-0 items-center justify-center rounded-full text-red-400 hover:bg-red-950 hover:text-red-300';
  removeButton.title = 'Remove column';
  removeButton.setAttribute('aria-label', 'Remove column');
  removeButton.innerHTML =
    '<i class="bi bi-x-lg block" aria-hidden="true"></i>';

  removeButton.addEventListener('click', () => {
    row.remove();
    refreshExportColumnOptions();
  });

  row.append(label, removeButton);

  return row;
}

function setExportColumns(names) {
  exportColumnRows?.replaceChildren(
    ...names.map((name) => buildExportColumnRow(name))
  );

  refreshExportColumnOptions();
}

function resetExportColumns() {
  setExportColumns([]);

  if (addExportColumn) {
    addExportColumn.value = '';
  }

  addExportColumnError?.classList.add('hidden');
}

function populateExportColumnOptions(fields) {
  exportColumnChoices = [
    ...BUILTIN_EXPORT_FIELDS.map(([name]) => name),
    ...fields
      .filter((field) => field.field_type !== 'user')
      .map((field) => field.name)
  ];

  refreshExportColumnOptions();
}

// ==================== End Export Modal (part 1) ====================

// Rebuild the datalist from all available column names minus the ones
// already selected as rows.
function refreshExportColumnOptions() {
  if (!exportColumnOptions) {
    return;
  }

  const selected = new Set(
    [...exportColumnRows.querySelectorAll('.export-column-name')].map(
      (label) => label.textContent.toLowerCase()
    )
  );

  exportColumnOptions.replaceChildren(
    ...exportColumnChoices
      .filter((name) => !selected.has(name.toLowerCase()))
      .map((name) => new Option(name, name))
  );
}

function addExportColumnByName(rawName) {
  const name = rawName.trim();

  if (!name) {
    return;
  }

  const available = new Set(
    exportColumnChoices.map((choice) => choice.toLowerCase())
  );

  const existing = new Set(
    [...exportColumnRows.querySelectorAll('.export-column-name')].map(
      (label) => label.textContent.toLowerCase()
    )
  );

  const valid = available.has(name.toLowerCase()) && !existing.has(name.toLowerCase());

  addExportColumnError?.classList.toggle('hidden', valid);

  if (!valid) {
    return;
  }

  exportColumnRows?.append(buildExportColumnRow(name));

  refreshExportColumnOptions();

  addExportColumn.value = '';
}

// Open Export modal.

document
  .getElementById('export-button')
  ?.addEventListener('click', async () => {
    populateExportColumnOptions(await loadCustomFields());
    resetExportColumns();

    await loadExportTemplates();

    openModal(exportItemModal);
  });

// ==================== Export Templates ====================

const exportTemplateSelect = document.getElementById(
  'export-template-select'
);
const exportTemplateApplyButton = document.getElementById(
  'export-template-apply-button'
);
const exportTemplateName = document.getElementById('export-template-name');
const exportTemplateSaveButton = document.getElementById(
  'export-template-save-button'
);
const exportTemplateShared = document.getElementById(
  'export-template-shared'
);
const exportTemplateError = document.getElementById('export-template-error');

function selectedExportColumns() {
  return [
    ...exportColumnRows.querySelectorAll('.export-column-name')
  ].map((label) => label.textContent);
}

async function loadExportTemplates() {
  if (!exportTemplateSelect) {
    return;
  }

  let templates = [];

  try {
    const response = await fetch('/export-templates');

    templates = response.ok ? await response.json() : [];
  } catch (error) {
    console.error('Failed to load export templates:', error);
  }

  const options = [new Option('No template selected', '')];

  for (const template of templates) {
    const label = template.shared ? `${template.name} (shared)` : template.name;

    options.push(new Option(label, template.id));
  }

  exportTemplateSelect.replaceChildren(...options);
  exportTemplateApplyButton.disabled = true;
}

function showExportTemplateError(message) {
  if (!exportTemplateError) {
    return;
  }

  exportTemplateError.textContent = message;
  exportTemplateError.classList.remove('hidden');
}

exportTemplateSelect?.addEventListener('change', () => {
  exportTemplateApplyButton.disabled = !exportTemplateSelect.value;
});

exportTemplateApplyButton?.addEventListener('click', () => {
  if (!exportTemplateSelect.value) {
    return;
  }

  window.location.assign(
    `/export-templates/${exportTemplateSelect.value}/apply`
  );
});

exportTemplateSaveButton?.addEventListener('click', async () => {
  if (!exportTemplateName) {
    return;
  }

  const name = exportTemplateName.value.trim();

  if (!name) {
    showExportTemplateError('Enter a template name.');
    return;
  }

  exportTemplateError?.classList.add('hidden');

  const columns = selectedExportColumns();

  const configuration = columns.length ? { columns } : {};

  try {
    const response = await fetch('/export-templates', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token':
          document.querySelector('input[name="csrf_token"]')?.value ?? ''
      },
      body: JSON.stringify({
        name,
        configuration,
        shared: exportTemplateShared?.checked ?? false
      })
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));

      showExportTemplateError(body.error || 'Failed to save template.');
      return;
    }

    exportTemplateName.value = '';

    if (exportTemplateShared) {
      exportTemplateShared.checked = false;
    }

    await loadExportTemplates();
  } catch (error) {
    console.error('Failed to save export template:', error);
    showExportTemplateError('Failed to save template.');
  }
});

// ==================== End Export Templates ====================

function submitExportColumn() {
  addExportColumnByName(addExportColumn.value);
}

// Hide the error while typing a new value.
addExportColumn?.addEventListener('input', () => {
  addExportColumnError?.classList.add('hidden');
});

// Add a column when Enter is pressed instead of submitting the form.

addExportColumn?.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter') {
    return;
  }

  event.preventDefault();

  submitExportColumn();
});

// Add a column via the explicit Add button.

addExportColumnButton?.addEventListener('click', submitExportColumn);

// Reset to all fields.

exportColumnsReset?.addEventListener('click', resetExportColumns);

// Trigger the export with the selected columns.

exportForm?.addEventListener('submit', (event) => {
  event.preventDefault();

  const params = new URLSearchParams();

  for (const label of exportColumnRows.querySelectorAll(
    '.export-column-name'
  )) {
    params.append('fields', label.textContent);
  }

  const queryString = params.toString();

  window.location.assign(
    queryString ? `/inventory/export?${queryString}` : '/inventory/export'
  );

  closeModal();
});

// ==================== End Export Modal ====================
