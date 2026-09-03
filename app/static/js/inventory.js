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

  hint.className = 'mb-2 flex items-center gap-1.5';

  const typeBadge = document.createElement('span');

  typeBadge.className = 'rounded bg-zinc-700 px-1.5 py-0.5 text-xs text-zinc-300';
  typeBadge.textContent = CUSTOM_FIELD_TYPE_LABELS[field.field_type];

  hint.append(typeBadge);

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

const DECIMAL_PATTERN = /^[+-]?[0-9]+(\.[0-9]+)?$/;

// Validate decimal input as the user types: strip illegal characters and
// block submit until the value is a valid number.
function attachDecimalValidation(input) {
  const validate = () => {
    if (input.value === '' || DECIMAL_PATTERN.test(input.value)) {
      input.setCustomValidity('');
    } else {
      input.setCustomValidity('Enter a valid number');
      input.reportValidity();
    }
  };

  input.addEventListener('input', () => {
    const caret = input.selectionStart;
    const originalLength = input.value.length;

    // Drop anything that cannot appear in a decimal number, then keep a
    // single leading sign and a single decimal point.
    let cleaned = input.value.replace(/[^0-9.+-]/g, '');
    cleaned = cleaned.replace(/(?!^)[+-]/g, '');

    const firstDot = cleaned.indexOf('.');

    if (firstDot !== -1) {
      cleaned =
        cleaned.slice(0, firstDot + 1) +
        cleaned.slice(firstDot + 1).replace(/\./g, '');
    }

    if (cleaned !== input.value) {
      input.value = cleaned;

      const removed = originalLength - cleaned.length;
      const position = Math.max(0, (caret ?? cleaned.length) - removed);

      input.setSelectionRange(position, position);
    }

    validate();
  });

  validate();
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
      input.placeholder = 'Enter integer';
    } else if (field.field_type === 'decimal') {
      // A number input can block decimals; accept any text and validate
      // the pattern client-side as the user types.
      input.type = 'text';
      input.inputMode = 'decimal';
      input.placeholder = 'Enter decimal';
      input.pattern = '[+-]?[0-9]+(\\.[0-9]+)?';
      input.title = 'Enter a number';
      attachDecimalValidation(input);
    } else if (field.field_type === 'date') {
      input.type = 'date';
    } else {
      input = document.createElement('textarea');
      input.className =
        'form-input description-textarea !resize-none overflow-hidden min-h-16';
      input.name = name;
      input.rows = '1';
      input.placeholder = `Enter ${field.name.toLowerCase()}`;
      attachAutoResize(input);
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

    if (input.tagName === 'TEXTAREA') {
      autoResize(input);
    }
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

const EMPTY_FILTER_VALUE = '__empty__';

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
    ['<=', 'Until'],
    ['>', 'After'],
    ['>=', 'Since']
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

  if (field.field_type === 'boolean') {
    control = document.createElement('select');
    control.className = 'form-select';
    control.name = 'f_value';

    // "—" filters items with no stored value for the field.
    control.append(new Option('—', EMPTY_FILTER_VALUE));

    control.append(new Option('True', 'true'), new Option('False', 'false'));

    return control;
  }

  if (field.field_type === 'enum') {
    control = document.createElement('select');
    control.className = 'form-select';
    control.name = 'f_value';

    for (const value of field.enum_values ?? []) {
      control.append(new Option(value, value));
    }

    return control;
  }

  control = document.createElement('input');
  control.className = 'form-input min-w-0 flex-1';
  control.name = 'f_value';

  if (field.field_type === 'integer') {
    control.type = 'number';
    control.step = '1';
  } else if (field.field_type === 'decimal') {
    control.type = 'text';
    control.inputMode = 'decimal';
    control.pattern = '[+-]?[0-9]+(\\.[0-9]+)?';
    control.title = 'Enter a number';
    attachDecimalValidation(control);
  } else if (field.field_type === 'date') {
    control.type = 'date';
  } else {
    control.type = 'text';
  }

  return control;
}

function updateFilterRowControls(row, field) {
  const selectsLine = row.querySelector('.cf-filter-selects');
  const controls = row.querySelector('.cf-filter-controls');

  controls.replaceChildren();

  // Remove any operator or value control left by the previous field type.
  selectsLine.querySelector('.cf-filter-op-wrap')?.remove();
  selectsLine.querySelector('.cf-filter-value-wrap')?.remove();

  const operators = operatorOptionsFor(field.field_type);

  if (operators.length > 0) {
    const opSelect = document.createElement('select');

    opSelect.className = 'form-select cf-filter-op w-28';
    opSelect.name = 'f_op';
    opSelect.setAttribute('aria-label', 'Operator');

    // "—" filters items with no stored value; it is the default operator.
    opSelect.append(new Option('—', EMPTY_FILTER_VALUE));

    for (const [value, label] of operators) {
      opSelect.append(new Option(label, value));
    }

    const opWrap = wrapSelectWithChevron(opSelect);

    opWrap.classList.add('cf-filter-op-wrap', 'shrink-0');

    selectsLine.append(opWrap);

    let matchCaseLabel = null;

    if (field.field_type === 'text') {
      const matchCase = document.createElement('input');

      matchCase.type = 'checkbox';
      matchCase.className = 'cf-filter-match-case h-4 w-4 rounded border-zinc-600 bg-zinc-800 text-zinc-100 focus:ring-zinc-500';
      matchCase.title = 'Match case';

      matchCase.addEventListener('change', () => {
        for (const option of opSelect.options) {
          if (option.value === EMPTY_FILTER_VALUE) {
            continue;
          }

          option.value = matchCase.checked ? `${option.value}_cs` : option.value.replace('_cs', '');
        }
      });

      matchCaseLabel = document.createElement('label');

      // Aligned with the text inside the value input above it.
      matchCaseLabel.className = 'ml-3 flex items-center gap-1 text-xs text-zinc-400 whitespace-nowrap';
      matchCaseLabel.append(matchCase, document.createTextNode('Match Case'));
    }

    const valueControl = buildFilterValueControl(field);

    let valueNode = valueControl;

    if (valueControl.tagName === 'SELECT') {
      valueNode = wrapSelectWithChevron(valueControl);
      valueNode.classList.add('cf-filter-value-wrap', 'flex-1');
    }

    const hiddenValue = document.createElement('input');

    hiddenValue.type = 'hidden';
    hiddenValue.name = 'f_value';
    hiddenValue.value = EMPTY_FILTER_VALUE;

    const inputLine = document.createElement('div');

    inputLine.className = 'flex w-full items-center gap-2';

    inputLine.append(valueNode, hiddenValue);

    const valueRow = document.createElement('div');

    valueRow.className = 'flex w-full flex-col gap-2';

    valueRow.append(inputLine);

    if (matchCaseLabel) {
      valueRow.append(matchCaseLabel);
    }

    // The value row is hidden while "—" filters for items with no stored
    // value; the hidden sentinel is submitted instead of the value control.
    const applyMode = () => {
      const isEmpty = opSelect.value === EMPTY_FILTER_VALUE;

      valueRow.classList.toggle('hidden', isEmpty);
      valueControl.disabled = isEmpty;
      hiddenValue.disabled = !isEmpty;
    };

    opSelect.addEventListener('change', applyMode);
    applyMode();

    controls.append(valueRow);
  } else {
    // Boolean rows have no operator control; the server treats them as "=".
    const op = document.createElement('input');

    op.type = 'hidden';
    op.name = 'f_op';
    op.value = '=';

    controls.append(op);

    const valueControl = buildFilterValueControl(field);

    const valueWrap = wrapSelectWithChevron(valueControl);

    valueWrap.classList.add('cf-filter-value-wrap', 'min-w-0', 'flex-1');

    selectsLine.append(valueWrap);
  }
}

function buildFilterRow(fields) {
  const row = document.createElement('div');

  row.className =
    'cf-filter-row flex items-center gap-2 rounded-lg border border-zinc-800 p-2';

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

  const fieldWrap = wrapSelectWithChevron(fieldSelect);

  fieldWrap.classList.add('min-w-0', 'flex-1');

  // Field and operator share one line that stretches to the remove button;
  // the value control gets its own line below.
  const selectsLine = document.createElement('div');

  selectsLine.className = 'cf-filter-selects flex items-center gap-2';

  selectsLine.append(fieldWrap);

  const controls = document.createElement('div');

  controls.className = 'cf-filter-controls contents';

  const content = document.createElement('div');

  content.className = 'flex min-w-0 flex-1 flex-col items-stretch gap-2';

  content.append(selectsLine, controls);

  row.append(content, removeButton);

  removeButton.classList.add('shrink-0');

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

  if (!filterForm.checkValidity()) {
    filterForm.reportValidity();
    return;
  }

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

function attachAutoResize(textArea) {
  textArea.addEventListener('input', () => {
    autoResize(textArea);
  });

  autoResize(textArea);
}

for (const textArea of document.querySelectorAll('.description-textarea')) {
  attachAutoResize(textArea);
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

  if (!editItemForm.checkValidity()) {
    editItemForm.reportValidity();
    return;
  }

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


// ==================== Export Modal ====================

// Keep in sync with _BUILTIN_COLUMNS in app/services/export.py.
const BUILTIN_EXPORT_FIELDS = [
  ['id', 'ID'],
  ['name', 'Name'],
  ['description', 'Description'],
  ['location', 'Location'],
  ['created_at', 'Created at'],
  ['updated_at', 'Updated at']
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

// Full list of available column names; the datalist excludes the columns
// that are already selected.
let exportColumnChoices = [];

// Columns contributed by the currently active filters: the location filter
// contributes "location", each field-filter row contributes its custom
// field, and "id" and "name" are always included alongside them so
// exported rows stay identifiable. Empty when no field-bearing filter is
// active.
async function collectActiveFilterColumns() {
  const columns = [];

  if (getInventoryParams().get('location_id')) {
    columns.push('location');
  }

  const fields = await loadCustomFields();
  const fieldsById = new Map(
    fields.map((field) => [String(field.id), field])
  );

  for (const row of customFieldFilterRows?.querySelectorAll(
    '.cf-filter-row'
  ) ?? []) {
    const field = fieldsById.get(row.querySelector('.cf-filter-field')?.value);

    // Rows without a chosen field are not active filters.
    if (field && field.field_type !== 'user' && !columns.includes(field.name)) {
      columns.push(field.name);
    }
  }

  if (columns.length > 0) {
    // Exported rows must stay identifiable.
    columns.unshift('id', 'name');
  }

  return columns;
}

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
    loadLocations();

    populateExportColumnOptions(await loadCustomFields());
    resetExportColumns();
    setExportColumns(await collectActiveFilterColumns());

    openModal(exportItemModal);
  });


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


// Trigger the export with the current filters and selected columns.

exportForm?.addEventListener('submit', (event) => {
  event.preventDefault();

  const params = getInventoryParams();

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
