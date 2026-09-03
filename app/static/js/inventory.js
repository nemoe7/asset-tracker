// ==================== Inventory List ====================

const inventoryContent = document.getElementById('inventory-content');
const inventoryLoading = document.getElementById('inventory-loading');
const searchInput = document.getElementById('search');
const filterForm = document.getElementById('filter-form');
const filterSortBy = document.getElementById('filter-sort-by');
const includeArchived = document.querySelector(
  'input[name="include_archived"]'
);

const addItemLocation = document.getElementById('item-location');
const editItemLocation = document.getElementById('edit-item-location');

let inventorySearchTimeout = null;
let inventoryRequest = null;
let currentInventoryPage = 1;




// ==================== Inventory Query Params ====================

function getInventoryParams() {
  const params = new URLSearchParams();

  const search = searchInput?.value.trim();

  if (search) {
    params.set('search', search);
  }

  if (filterForm) {
    const formData = new FormData(filterForm);

    for (const [name, value] of formData.entries()) {
      if (name === 'search') {
        continue;
      }

      if (value) {
        params.append(name, value);
      }
    }
  }

  return params;
}

function updateExportHref() {
  const exportButton = document.getElementById('export-button');

  if (!exportButton) {
    return;
  }

  const params = getInventoryParams();

  const queryString = params.toString();

  exportButton.href = queryString
    ? `/inventory/export?${queryString}`
    : '/inventory/export';
}

// ==================== End Inventory Query Params ====================


// ==================== End Inventory List ====================


// ==================== Load Inventory ====================

async function loadInventory(page = 1) {
  if (!inventoryContent) {
    return;
  }

  currentInventoryPage = page;

  inventoryLoading?.classList.remove('hidden');
  inventoryContent.classList.add('hidden');

  inventoryRequest?.abort();
  inventoryRequest = new AbortController();

  const params = getInventoryParams();

  params.set('page', page);

  updateExportHref();
  // params.set('per_page', 2);

  try {
    const response = await fetch(
      `/inventory/fragment?${params.toString()}`,
      {
        signal: inventoryRequest.signal
      }
    );

    if (!response.ok) {
      if (response.status === 400) {
        inventoryContent.innerHTML = `
          <div class="flex flex-col items-center justify-center py-12 text-center">
            <p class="text-sm text-zinc-400">
              Invalid inventory filters.
            </p>

            <button
              type="button"
              id="reset-inventory-filters"
              class="mt-3 text-sm text-zinc-200 underline hover:text-white"
            >
              Reset filters
            </button>
          </div>
        `;

        document
          .getElementById('reset-inventory-filters')
          ?.addEventListener('click', () => {
            resetInventoryFilters();
            loadInventory(1);
          });
      } else {
        inventoryContent.innerHTML = `
          <div class="flex flex-col items-center justify-center py-12 text-center">
            <p class="text-sm text-zinc-400">
              Failed to load inventory.
            </p>

            <button
              type="button"
              id="retry-inventory"
              class="mt-3 text-sm text-zinc-200 underline hover:text-white"
            >
              Try again
            </button>
          </div>
        `;

        document
          .getElementById('retry-inventory')
          ?.addEventListener('click', () => {
            loadInventory(currentInventoryPage);
          });
      }

      return;
    }

    inventoryContent.innerHTML = await response.text();
    bindInventoryActions();
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('Failed to load inventory:', error);
    }
  } finally {
    if (!inventoryRequest.signal.aborted) {
      inventoryLoading?.classList.add('hidden');
      inventoryContent.classList.remove('hidden');
    }
  }
}

// ==================== End Load Inventory ====================


// ==================== Bind Inventory Actions ====================

function bindInventoryActions() {
  for (const button of inventoryContent.querySelectorAll('.copy-item-id')) {
    button.addEventListener('click', handleCopyItemId);
  }

  for (const button of inventoryContent.querySelectorAll('.edit-item')) {
    button.addEventListener('click', handleEditItem);
  }

  for (const button of inventoryContent.querySelectorAll('.restore-item')) {
    button.addEventListener('click', handleRestoreItem);
  }

  for (const item of inventoryContent.querySelectorAll('.view-item')) {
    item.addEventListener('click', handleViewItem);
  }

  for (const button of inventoryContent.querySelectorAll('.inventory-page')) {
    button.addEventListener('click', () => {
      const page = Number(button.dataset.page);

      if (page) {
        loadInventory(page);
      }
    });
  }
}

// ==================== End Bind Inventory Actions ====================


// ==================== Copy Asset ID ====================

async function handleCopyItemId(event) {
  event.stopPropagation();

  const button = event.currentTarget;
  const itemId = button.dataset.itemId;

  if (!itemId) {
    return;
  }

  await navigator.clipboard.writeText(itemId);

  const icon = button.querySelector('i');

  if (!icon) {
    return;
  }

  icon.classList.remove('bi-copy');
  icon.classList.add('bi-check-lg');

  setTimeout(() => {
    icon.classList.remove('bi-check-lg');
    icon.classList.add('bi-copy');
  }, 1500);
}

// ==================== End Copy Asset ID ====================


// ==================== QR Scanner ====================

const qrScannerButton = document.getElementById('qr-scanner-button');
const qrScannerModal = document.getElementById('qr-scanner-modal');
const qrReader = document.getElementById('qr-reader');
const qrScannerError = document.getElementById('qr-scanner-error');

let qrScanner = null;
let qrScannerRunning = false;
let qrScannerProcessing = false;

// Initialize QR scanner.

async function startQrScanner() {
  if (!qrReader || qrScannerRunning) {
    return;
  }

  qrScanner = new Html5Qrcode('qr-reader');
  qrScannerProcessing = false;


  await qrScanner.start(
    {
      facingMode: 'environment'
    },
    {
      fps: 10,
      qrbox: {
        width: 250,
        height: 250
      }
    },
    async (decodedText) => {
      if (qrScannerProcessing) {
        return;
      }

      qrScannerProcessing = true;

      qrScannerError.classList.add('hidden');
      const itemId = decodedText.trim();

      if (!itemId) {
        qrScannerProcessing = false;
        return;
      }

      const response = await fetch(
        `/inventory/${encodeURIComponent(itemId)}/check`,
        {
          method: 'POST'
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        qrScannerError.textContent = data.error;
        qrScannerError.classList.remove('hidden');
        qrScannerProcessing = false;
        return;
      }

      const item = await response.json();

      await stopQrScanner();
      openViewItem(item.id);
    },
    () => {
      // Ignore scan failures while looking for a QR code.
    }
  );

  const video = qrReader.querySelector('video');

  if (video) {
    video.classList.add('w-full', 'h-auto');
    video.style.removeProperty('width');
    video.style.removeProperty('height');
  }

  qrScannerRunning = true;
  qrReader.classList.remove('hidden');
}


// Stop QR scanner.

async function stopQrScanner() {
  if (!qrScanner || !qrScannerRunning) {
    return;
  }

  await qrScanner.stop();
  qrScanner.clear();

  qrScanner = null;
  qrScannerRunning = false;
  qrReader.classList.add('hidden');
}


// Stop the QR scanner when the modal manager closes.

onModalClose(async () => {
  if (qrScannerRunning) {
    await stopQrScanner();
  }
});


// Open QR scanner.

qrScannerButton?.addEventListener('click', () => {
  openModal(qrScannerModal, async () => {
    await new Promise((resolve) => {
      requestAnimationFrame(resolve);
    });

    await startQrScanner();
  });
});

// ==================== End QR Scanner ====================


// ==================== Custom Fields ====================

const addItemCustomFields = document.getElementById('add-item-custom-fields');
const editItemCustomFields = document.getElementById('edit-item-custom-fields');
const viewItemCustomFields = document.getElementById('view-item-custom-fields');

let customFieldsCache = null;

async function loadCustomFields() {
  if (customFieldsCache) {
    return customFieldsCache;
  }

  try {
    const response = await fetch('/custom-fields');

    customFieldsCache = response.ok ? await response.json() : [];
  } catch (error) {
    console.error('Failed to load custom fields:', error);
    customFieldsCache = [];
  }

  return customFieldsCache;
}

function formatCustomFieldValue(value) {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  if (value === true) {
    return 'True';
  }

  if (value === false) {
    return 'False';
  }

  return String(value);
}

const CUSTOM_FIELD_TYPE_LABELS = {
  text: 'Text',
  integer: 'Integer',
  decimal: 'Decimal',
  boolean: 'Boolean',
  date: 'Date',
  enum: 'Enum'
};

function wrapSelectWithChevron(select) {
  const wrapper = document.createElement('div');

  wrapper.className = 'relative';

  const chevron = document.createElement('i');

  chevron.className =
    'bi bi-chevron-down pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400';
  chevron.setAttribute('aria-hidden', 'true');

  wrapper.append(select, chevron);

  return wrapper;
}

function appendCustomFieldHint(element, field) {
  // Type hint and Required badge under the field name (Add/Edit modals).
  if (!CUSTOM_FIELD_TYPE_LABELS[field.field_type]) {
    return;
  }

  const hint = document.createElement('div');

  hint.className = 'mb-2 flex items-center gap-1.5 text-xs text-zinc-500';
  hint.textContent = CUSTOM_FIELD_TYPE_LABELS[field.field_type];

  if (field.required) {
    const badge = document.createElement('span');

    badge.className = 'rounded bg-zinc-700 px-1.5 py-0.5 text-xs text-zinc-300';
    badge.textContent = 'Required';

    hint.append(badge);
  }

  element.append(hint);
}

function appendDescriptionIcon(element, description) {
  // Hover tooltip only for fields that actually have a description.
  if (!description) {
    return;
  }

  const icon = document.createElement('i');

  icon.className = 'bi bi-question-circle ml-1 text-zinc-500';
  icon.title = description;

  element.append(icon);
}

function buildCustomFieldInput(field) {
  if (field.field_type === 'user') {
    return null;
  }

  const name = `f_${field.name}`;
  let input;

  if (field.field_type === 'boolean' || field.field_type === 'enum') {
    input = document.createElement('select');
    input.className = 'form-select';
    input.name = name;

    input.append(new Option('—', ''));

    if (field.field_type === 'boolean') {
      input.append(new Option('True', 'true'), new Option('False', 'false'));
    } else {
      for (const value of field.enum_values ?? []) {
        input.append(new Option(value, value));
      }
    }
  } else {
    input = document.createElement('input');
    input.className = 'form-input';
    input.name = name;

    if (field.field_type === 'integer') {
      input.type = 'number';
      input.step = '1';
      input.placeholder = 'e.g. 42';
    } else if (field.field_type === 'decimal') {
      // A number input can block decimals; accept any text and rely on
      // server-side validation instead.
      input.type = 'text';
      input.inputMode = 'decimal';
      input.placeholder = 'e.g. 3.14';
    } else if (field.field_type === 'date') {
      input.type = 'date';
    } else {
      input.type = 'text';
      input.placeholder = `Enter ${field.name.toLowerCase()}`;
    }
  }

  if (field.required) {
    input.required = true;
  }

  return input;
}

function setCustomFieldValue(input, value) {
  if (value === null || value === undefined) {
    return;
  }

  if (input.type === 'select-one' || input.tagName === 'SELECT') {
    input.value = value === true ? 'true' : value === false ? 'false' : String(value);
    return;
  }

  input.value = String(value);
}

function clearCustomFieldRows(container) {
  for (const row of [...container.querySelectorAll('tr.cf-row')]) {
    row.remove();
  }
}

function renderAddItemCustomFields(fields) {
  if (!addItemCustomFields) {
    return;
  }

  addItemCustomFields.replaceChildren();

  for (const field of fields) {
    const input = buildCustomFieldInput(field);

    if (!input) {
      continue;
    }

    const label = document.createElement('label');

    label.className = 'mb-1 block text-sm font-medium text-zinc-300';
    label.htmlFor = input.id = `add-cf-${field.id}`;
    label.textContent = field.name;

    appendDescriptionIcon(label, field.description);

    const wrapper = document.createElement('div');

    wrapper.append(label);
    appendCustomFieldHint(wrapper, field);
    wrapper.append(
      input.tagName === 'SELECT' ? wrapSelectWithChevron(input) : input
    );
    addItemCustomFields.append(wrapper);
  }
}

function renderEditItemCustomFields(fields, valuesByName) {
  if (!editItemCustomFields) {
    return;
  }

  clearCustomFieldRows(editItemCustomFields);

  for (const field of fields) {
    const input = buildCustomFieldInput(field);

    if (!input) {
      continue;
    }

    setCustomFieldValue(input, valuesByName[field.name]);

    const label = document.createElement('th');

    label.className = 'w-1/3 px-4 py-3 font-medium text-zinc-400';

    const name = document.createElement('div');

    name.className = 'mb-1';
    name.textContent = field.name;

    appendDescriptionIcon(name, field.description);
    label.append(name);
    appendCustomFieldHint(label, field);

    const cell = document.createElement('td');

    cell.className = 'px-4 py-3';
    cell.append(
      input.tagName === 'SELECT' ? wrapSelectWithChevron(input) : input
    );

    const row = document.createElement('tr');

    row.className = 'cf-row';
    row.append(label, cell);
    editItemCustomFields.append(row);
  }
}

function renderViewItemCustomFields(fields, valuesByName) {
  if (!viewItemCustomFields) {
    return;
  }

  clearCustomFieldRows(viewItemCustomFields);

  for (const field of fields) {
    const label = document.createElement('th');

    label.className = 'w-1/3 px-4 py-3 font-medium text-zinc-400';
    label.textContent = field.name;

    appendDescriptionIcon(label, field.description);

    const cell = document.createElement('td');

    cell.className = 'px-4 py-3 text-zinc-100';
    cell.textContent = formatCustomFieldValue(valuesByName[field.name]);

    const row = document.createElement('tr');

    row.className = 'cf-row';
    row.append(label, cell);
    viewItemCustomFields.append(row);
  }
}

// ==================== End Custom Fields ====================


// ==================== Field Filters (Filter Modal) ====================

const customFieldFilterRows = document.getElementById(
  'custom-field-filter-rows'
);
const addFieldFilterButton = document.getElementById(
  'add-field-filter-button'
);

const FILTER_OPERATORS = {
  integer: [
    ['=', '='],
    ['!=', '!='],
    ['<', '<'],
    ['<=', '<='],
    ['>', '>'],
    ['>=', '>=']
  ],
  decimal: [
    ['=', '='],
    ['!=', '!='],
    ['<', '<'],
    ['<=', '<='],
    ['>', '>'],
    ['>=', '>=']
  ],
  date: [
    ['=', 'On'],
    ['!=', 'Not on'],
    ['<', 'Before'],
    ['<=', 'No later than'],
    ['>', 'After'],
    ['>=', 'No earlier than']
  ],
  enum: [
    ['=', 'Is'],
    ['!=', 'Is not']
  ],
  boolean: [],
  text: [
    ['contains', 'Contains'],
    ['excludes', 'Excludes']
  ]
};

function operatorOptionsFor(fieldType) {
  return FILTER_OPERATORS[fieldType] ?? [];
}

function buildFilterValueControl(field) {
  let control;

  if (field.field_type === 'boolean' || field.field_type === 'enum') {
    control = document.createElement('select');
    control.className = 'form-select';
    control.name = 'f_value';

    control.append(new Option('—', ''));

    if (field.field_type === 'boolean') {
      control.append(new Option('True', 'true'), new Option('False', 'false'));
    } else {
      for (const value of field.enum_values ?? []) {
        control.append(new Option(value, value));
      }
    }
  } else {
    control = document.createElement('input');
    control.className = 'form-input';
    control.name = 'f_value';

    if (field.field_type === 'integer') {
      control.type = 'number';
      control.step = '1';
    } else if (field.field_type === 'decimal') {
      control.type = 'text';
      control.inputMode = 'decimal';
    } else if (field.field_type === 'date') {
      control.type = 'date';
    } else {
      control.type = 'text';
    }
  }

  return control;
}

function updateFilterRowControls(row, field) {
  const controls = row.querySelector('.cf-filter-controls');

  controls.replaceChildren();

  const operators = operatorOptionsFor(field.field_type);

  if (operators.length > 0) {
    const opSelect = document.createElement('select');

    opSelect.className = 'form-select cf-filter-op';
    opSelect.name = 'f_op';
    opSelect.setAttribute('aria-label', 'Operator');

    for (const [value, label] of operators) {
      opSelect.append(new Option(label, value));
    }

    controls.append(wrapSelectWithChevron(opSelect));

    if (field.field_type === 'text') {
      const matchCase = document.createElement('input');

      matchCase.type = 'checkbox';
      matchCase.className = 'cf-filter-match-case h-4 w-4 rounded border-zinc-600 bg-zinc-800 text-zinc-100 focus:ring-zinc-500';
      matchCase.title = 'Match case';

      matchCase.addEventListener('change', () => {
        for (const option of opSelect.options) {
          option.value = matchCase.checked ? `${option.value}_cs` : option.value.replace('_cs', '');
        }
      });

      const matchCaseLabel = document.createElement('label');

      matchCaseLabel.className = 'flex items-center gap-1 text-xs text-zinc-400 whitespace-nowrap';
      matchCaseLabel.append(matchCase, document.createTextNode('Aa'));

      controls.append(matchCaseLabel);
    }
  } else {
    // Boolean rows have no operator control; the server treats them as "=".
    const op = document.createElement('input');

    op.type = 'hidden';
    op.name = 'f_op';
    op.value = '=';

    controls.append(op);
  }

  const valueControl = buildFilterValueControl(field);

  controls.append(
    valueControl.tagName === 'SELECT' ? wrapSelectWithChevron(valueControl) : valueControl
  );
}

function buildFilterRow(fields) {
  const row = document.createElement('div');

  row.className = 'cf-filter-row space-y-2 rounded-lg border border-zinc-800 p-3';

  const header = document.createElement('div');

  header.className = 'flex items-center gap-2';

  const fieldSelect = document.createElement('select');

  fieldSelect.className = 'form-select cf-filter-field';
  fieldSelect.name = 'f_field';
  fieldSelect.setAttribute('aria-label', 'Field');

  fieldSelect.append(new Option('—', ''));

  for (const field of fields) {
    if (field.field_type !== 'user') {
      fieldSelect.append(new Option(field.name, field.id));
    }
  }

  const removeButton = document.createElement('button');

  removeButton.type = 'button';
  removeButton.className = 'cf-filter-row-remove icon-button text-red-400 hover:bg-red-950 hover:text-red-300';
  removeButton.title = 'Remove filter';
  removeButton.setAttribute('aria-label', 'Remove filter');
  removeButton.innerHTML = '<i class="bi bi-x-lg block size-3.5" aria-hidden="true"></i>';

  removeButton.addEventListener('click', () => {
    row.remove();
  });

  header.append(wrapSelectWithChevron(fieldSelect), removeButton);

  const controls = document.createElement('div');

  controls.className = 'cf-filter-controls flex items-center gap-2';

  row.append(header, controls);

  fieldSelect.addEventListener('change', () => {
    const field = fields.find((candidate) => candidate.id == fieldSelect.value);

    if (field) {
      updateFilterRowControls(row, field);
    } else {
      controls.replaceChildren();
    }
  });

  return row;
}

function populateFilterSortBy(fields) {
  if (!filterSortBy) {
    return;
  }

  const selectedValue = filterSortBy.value;

  for (const field of fields) {
    if (field.field_type !== 'user' && !filterSortBy.querySelector(`option[value="${field.id}"]`)) {
      filterSortBy.append(new Option(field.name, field.id));
    }
  }

  filterSortBy.value = selectedValue;
}

addFieldFilterButton?.addEventListener('click', async () => {
  const fields = await loadCustomFields();

  customFieldFilterRows?.append(buildFilterRow(fields));
});

// ==================== End Field Filters (Filter Modal) ====================


// ==================== Filter & Sort Modal ====================

const filterItemButton = document.getElementById('filter-item-button');
const filterItemModal = document.getElementById('filter-item-modal');
const clearFilterItem = document.getElementById('clear-filter-item');

const filterLocation = document.getElementById('filter-location');


// Load current locations.

async function loadLocations() {
  try {
    const response = await fetch('/locations');

    if (!response.ok) {
      return;
    }

    const locations = await response.json();

    if (filterLocation) {
      const selectedValue = filterLocation.value;

      filterLocation.replaceChildren(
        new Option('<All Locations>', ''),
        new Option('<No Location>', '__none__')
      );

      for (const location of locations) {
        filterLocation.append(
          new Option(location.name, location.id)
        );
      }

      filterLocation.value = selectedValue;
    }

    for (const select of [addItemLocation, editItemLocation]) {
      if (!select) {
        continue;
      }

      const selectedValue = select.value;

      select.replaceChildren(
        new Option('—', '')
      );

      for (const location of locations) {
        select.append(
          new Option(location.name, location.id)
        );
      }

      select.value = selectedValue;
    }
  } catch (error) {
    console.error('Failed to load locations:', error);
  }
}


// Open Filter & Sort modal.

filterItemButton?.addEventListener('click', () => {
  loadLocations();
  loadCustomFields().then(populateFilterSortBy);
  openModal(filterItemModal);
});


// Clear filters.

clearFilterItem?.addEventListener('click', () => {
  filterForm?.reset();
  customFieldFilterRows?.replaceChildren();
  resetInventoryFilters();
  loadInventory(1);
  closeModal();
});


// Apply filters without navigating.

filterForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  loadInventory(1);
  closeModal();
});

// ==================== End Filter & Sort Modal ====================


// ==================== Add Item Modal ====================

const addItemModal = document.getElementById('add-item-modal');


// Open dynamically loaded Add Item button.

document.addEventListener('click', (event) => {
  if (event.target.closest('#empty-add-item-button')) {
    loadLocations();
    loadCustomFields().then(renderAddItemCustomFields);
    openModal(addItemModal);
  }
});


// Open Add Item modal.

document
  .getElementById('add-item-button')
  ?.addEventListener('click', () => {
    loadLocations();
    loadCustomFields().then(renderAddItemCustomFields);
    openModal(addItemModal);
  });

document
  .getElementById('cancel-add-item')
  ?.addEventListener('click', () => {
    closeModal();
  });

// Handle description resize
function autoResize(textArea) {
  textArea.style.height = 'auto';
  textArea.style.height = `${textArea.scrollHeight}px`;
}

for (const textArea of document.querySelectorAll('.description-textarea')) {
  textArea.addEventListener('input', () => {
    autoResize(textArea);
  });

  autoResize(textArea);
}

// ==================== End Add Item Modal ====================


// ==================== Edit Asset Modal ====================

const editItemModal = document.getElementById('edit-item-modal');
const editItemForm = document.getElementById('edit-item-form');

const editItemId = document.getElementById('edit-item-id');
const editItemName = document.getElementById('edit-item-name');
const editItemDescription = document.getElementById('edit-item-description');

let currentEditItemId = null;


// Load an asset into the Edit Asset modal.

async function loadEditItem(itemId) {
  const response = await fetch(`/inventory/${itemId}`);

  if (!response.ok) {
    closeModal();
    return;
  }

  const item = await response.json();

  await loadLocations();

  editItemId.textContent = item.id;
  editItemName.value = item.name;
  editItemDescription.value = item.description ?? '';
  autoResize(editItemDescription);
  editItemLocation.value = item.location_id ?? '';
  editItemForm.action = `/inventory/${itemId}`;

  renderEditItemCustomFields(
    await loadCustomFields(),
    item.custom_fields ?? {}
  );
}


// Handle Edit Asset.

async function handleEditItem(event) {
  event.stopPropagation();

  const button = event.currentTarget;
  const itemId = button.dataset.itemId;

  if (!itemId) {
    return;
  }

  currentEditItemId = itemId;

  await openModal(editItemModal, () => loadEditItem(itemId));
}


// Submit Edit Asset without leaving the inventory page.

editItemForm?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const response = await fetch(
    editItemForm.action,
    {
      method: 'POST',
      body: new FormData(editItemForm)
    }
  );

  if (!response.ok) {
    return;
  }

  closeModal();
  loadInventory(currentInventoryPage);
});

// ==================== End Edit Asset Modal ====================


// ==================== View Asset Modal ====================

const viewItemModal = document.getElementById('view-item-modal');

const viewItemId = document.getElementById('view-item-id');
const viewItemName = document.getElementById('view-item-name');
const viewItemDescription = document.getElementById('view-item-description');
const viewItemLocation = document.getElementById('view-item-location');
const viewItemCopy = document.getElementById('view-item-copy');
const viewItemEdit = document.getElementById('view-item-edit');
const viewItemArchived = document.getElementById('view-item-archived');
const viewItemRestore = document.getElementById('view-item-restore');

let currentViewItemId = null;


// Open View Asset modal.

async function openViewItem(itemId) {
  if (!itemId) {
    return;
  }

  currentViewItemId = itemId;

  openModal(viewItemModal, async () => {
    const response = await fetch(
      `/inventory/${encodeURIComponent(itemId)}?include_archived=true`
    );

    if (!response.ok) {
      closeModal();
      return;
    }

    const asset = await response.json();
    const isArchived = Boolean(asset.archived_at);

    viewItemArchived.classList.toggle('hidden', !isArchived);
    viewItemEdit.classList.toggle('hidden', isArchived);
    viewItemRestore.classList.toggle('hidden', !isArchived);

    viewItemId.textContent = asset.id;
    viewItemName.textContent = asset.name;
    viewItemDescription.textContent = asset.description || '—';
    viewItemLocation.textContent = asset.location_name || '—';

    renderViewItemCustomFields(
      await loadCustomFields(),
      asset.custom_fields ?? {}
    );
  });
}


// Handle View Asset.

function handleViewItem(event) {
  if (event.target.closest('.copy-item-id, .edit-item, .restore-item')) {
    return;
  }

  openViewItem(event.currentTarget.dataset.itemId);
}


// Copy Asset ID from View Asset modal.

viewItemCopy?.addEventListener('click', async () => {
  if (!currentViewItemId) {
    return;
  }

  await navigator.clipboard.writeText(currentViewItemId);

  const icon = viewItemCopy.querySelector('i');

  if (!icon) {
    return;
  }

  icon.classList.remove('bi-copy');
  icon.classList.add('bi-check-lg');

  setTimeout(() => {
    icon.classList.remove('bi-check-lg');
    icon.classList.add('bi-copy');
  }, 1500);
});


// View → Edit.

viewItemEdit?.addEventListener('click', () => {
  if (!currentViewItemId) {
    return;
  }

  currentEditItemId = currentViewItemId;

  switchModal(editItemModal, () => loadEditItem(currentEditItemId));
});


// View → Restore.

viewItemRestore?.addEventListener('click', () => {
  if (!currentViewItemId) {
    return;
  }

  currentRestoreItemId = currentViewItemId;
  switchModal(restoreItemModal);
});

// ==================== End View Asset Modal ====================


// ==================== Archive Asset ====================

const archiveItemModal = document.getElementById('archive-item-modal');
const archiveItemButton = document.getElementById('archive-item-button');
const cancelArchiveItem = document.getElementById('cancel-archive-item');
const confirmArchiveItem = document.getElementById('confirm-archive-item');


// Open Archive confirmation.

archiveItemButton?.addEventListener('click', () => {
  if (!currentEditItemId) {
    return;
  }

  openModal(archiveItemModal);
});


// Cancel Archive.

cancelArchiveItem?.addEventListener('click', () => {
  closeModal();
});


// Confirm Archive.

confirmArchiveItem?.addEventListener('click', async () => {
  if (!currentEditItemId) {
    return;
  }

  const response = await fetch(
    `/inventory/${currentEditItemId}/archive`,
    {
      method: 'POST'
    }
  );

  if (!response.ok) {
    closeModal();
    return;
  }

  closeModal();
  loadInventory(currentInventoryPage);
});

// ==================== End Archive Asset ====================


// ==================== Restore Asset ====================

const restoreItemModal = document.getElementById('restore-item-modal');
const cancelRestoreItem = document.getElementById('cancel-restore-item');
const confirmRestoreItem = document.getElementById('confirm-restore-item');

let currentRestoreItemId = null;


// Handle Restore Asset.

function handleRestoreItem(event) {
  event.stopPropagation();

  const button = event.currentTarget;
  const itemId = button.dataset.itemId;

  if (!itemId) {
    return;
  }

  currentRestoreItemId = itemId;

  openModal(restoreItemModal);
}


// Cancel Restore.

cancelRestoreItem?.addEventListener('click', () => {
  closeModal();
});


// Confirm Restore.

confirmRestoreItem?.addEventListener('click', async () => {
  if (!currentRestoreItemId) {
    return;
  }

  const response = await fetch(
    `/inventory/${currentRestoreItemId}/restore`,
    {
      method: 'POST'
    }
  );

  if (!response.ok) {
    closeModal();
    return;
  }

  closeModal();
  loadInventory(currentInventoryPage);
});

// ==================== End Restore Asset ====================




// ==================== Search ====================

searchInput?.addEventListener('input', () => {
  clearTimeout(inventorySearchTimeout);

  inventorySearchTimeout = setTimeout(() => {
    loadInventory(1);
  }, 300);
});


// Prevent search form navigation.

document
  .getElementById('search-form')
  ?.addEventListener('submit', (event) => {
    event.preventDefault();
    loadInventory(1);
  });

// ==================== End Search ====================


// ==================== Initial Load ====================

function resetInventoryFilters() {
  if (filterSortBy) {
    filterSortBy.value = 'name';
  }

  const sortOrder = document.querySelector(
    'input[name="sort_order"][value="asc"]'
  );

  if (sortOrder) {
    sortOrder.checked = true;
  }

  if (includeArchived) {
    includeArchived.checked = false;
  }

  if (filterLocation) {
    filterLocation.value = '';
  }
}

resetInventoryFilters();
loadInventory();

// ==================== End Initial Load ====================
