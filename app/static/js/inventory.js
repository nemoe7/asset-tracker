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

  saveInventoryFilters();

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
              Invalid asset filters.
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
              Failed to load assets.
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

  for (const link of inventoryContent.querySelectorAll('.view-item-link')) {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      openViewItem(link.dataset.itemId);
    });
    link.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openViewItem(link.dataset.itemId);
      }
    });
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
          method: 'POST',
          headers: { 'X-CSRF-Token': document.querySelector('input[name="csrf_token"]')?.value ?? '' }
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

let usersCache = null;

async function loadUsers() {
  if (usersCache) {
    return usersCache;
  }

  try {
    const response = await fetch('/users');

    usersCache = response.ok ? await response.json() : [];
  } catch (error) {
    console.error('Failed to load users:', error);
    usersCache = [];
  }

  return usersCache;
}

// Build one shared <datalist> of usernames, referenced by every user-type
// input in Add/Edit/Filter controls.
async function attachUserDatalist(input) {
  const users = await loadUsers();

  let datalist = document.getElementById('user-field-datalist');

  if (!datalist) {
    datalist = document.createElement('datalist');
    datalist.id = 'user-field-datalist';

    for (const user of users) {
      datalist.append(new Option(user.name || user.username, user.username));
    }

    document.body.append(datalist);
  }

  input.setAttribute('list', 'user-field-datalist');
}

// Resolve a stored user ID to a display label: name, then username, then
// the raw ID for archived/missing references.
async function formatUserFieldValue(value) {
  const users = await loadUsers();
  const user = users.find((candidate) => String(candidate.id) === String(value));

  if (!user) {
    return `#${value}`;
  }

  return user.name || user.username;
}

function formatCustomFieldValue(value, fieldType) {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  if (value === true) {
    return 'True';
  }

  if (value === false) {
    return 'False';
  }

  if (fieldType === 'expiry_date' && value) {
    const parts = value.split('-').map(Number);
    const expiry = new Date(parts[0], parts[1] - 1, parts[2]);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (today >= expiry) {
      return 'Expired';
    }
    const daysLeft = Math.floor((expiry - today) / (1000 * 60 * 60 * 24));
    const dayWord = daysLeft === 1 ? 'day' : 'days';
    return `Expires in ${daysLeft} ${dayWord} [${value}]`;
  }

  return String(value);
}

const CUSTOM_FIELD_TYPE_LABELS = {
  text: 'Text',
  integer: 'Integer',
  decimal: 'Decimal',
  boolean: 'Boolean',
  date: 'Date',
  expiry_date: 'Expiry Date',
  enum: 'Enum',
  user: 'User'
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

  typeBadge.className = 'rounded border border-zinc-700 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-zinc-400';
  typeBadge.textContent = CUSTOM_FIELD_TYPE_LABELS[field.field_type];

  hint.append(typeBadge);

  if (field.required) {
    const badge = document.createElement('span');

    badge.className = 'rounded border border-zinc-700 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-zinc-400';
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
    } else     if (field.field_type === 'date' || field.field_type === 'expiry_date') {
      input.type = 'date';
    } else if (field.field_type === 'user') {
      // User picker: free text with datalist suggestions; submits username
      // and the backend resolves it to a user ID.
      input.type = 'text';
      input.placeholder = 'Enter username';
      attachUserDatalist(input);
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
  for (const row of [...container.querySelectorAll('.cf-row, .cf-filter-row')]) {
    row.remove();
  }
}

function renderAddItemCustomFields(fields) {
  if (!addItemCustomFields) {
    return;
  }

  addItemCustomFields.replaceChildren();

  for (const field of fields) {
    if (field.is_editable === false) {
      continue;
    }

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

async function renderEditItemCustomFields(fields, valuesByName) {
  if (!editItemCustomFields) {
    return;
  }

  clearCustomFieldRows(editItemCustomFields);

  for (const field of fields) {
    const input = buildCustomFieldInput(field);

    if (!input) {
      continue;
    }

    if (field.is_editable === false) {
      input.disabled = true;
    }

    if (field.field_type === 'user') {
      // Prefill with the username; archived/missing references cannot be
      // re-submitted by username, so the input stays empty.
      const stored = valuesByName[field.name];

      if (stored !== null && stored !== undefined && stored !== '') {
        const users = await loadUsers();
        const user = users.find(
          (candidate) => String(candidate.id) === String(stored)
        );

        if (user) {
          input.value = user.username;
        }
      }
    } else {
      setCustomFieldValue(input, valuesByName[field.name]);
    }

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

    if (field.field_type === 'user' && valuesByName[field.name] !== null && valuesByName[field.name] !== undefined && valuesByName[field.name] !== '') {
      formatUserFieldValue(valuesByName[field.name]).then((label) => {
        cell.textContent = label;
      });
    } else {
      cell.textContent = formatCustomFieldValue(valuesByName[field.name], field.field_type);
    }

    if (field.copyable) {
      const copyButton = document.createElement('button');
      copyButton.type = 'button';
      copyButton.className = 'ml-2 inline-flex items-center gap-1 rounded-lg border border-zinc-700 px-2 py-0.5 text-xs text-zinc-400 transition hover:bg-zinc-800 hover:text-zinc-100';
      copyButton.title = 'Copy value';
      copyButton.setAttribute('aria-label', 'Copy value');
      copyButton.innerHTML = '<i class="bi bi-copy block size-3" aria-hidden="true"></i>';
      copyButton.dataset.fieldValue = cell.textContent;
      copyButton.addEventListener('click', handleCopyFieldValue);
      cell.append(copyButton);
    }

    const row = document.createElement('tr');

    row.className = 'cf-row';
    row.append(label, cell);
    viewItemCustomFields.append(row);
  }
}

async function handleCopyFieldValue(event) {
  event.stopPropagation();

  const button = event.currentTarget;
  const value = button.dataset.fieldValue;

  if (!value) {
    return;
  }

  await navigator.clipboard.writeText(value);

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
  expiry_date: [
    ['is', 'Is'],
    ['before', 'Before'],
    ['expires_in', 'Expires in']
  ],
  enum: [
    ['=', 'Is'],
    ['!=', 'Is not']
  ],
  user: [
    ['=', 'Is'],
    ['!=', 'Is not'],
    ['~', 'Matches']
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

function buildFilterValueControl(field, op) {
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

  if (field.field_type === 'expiry_date') {
    if (op === 'is') {
      control = document.createElement('select');
      control.className = 'form-select';
      control.name = 'f_value';
      control.append(new Option('Expired', 'expired'), new Option('Not Expired', 'not expired'));
      return control;
    }

    control = document.createElement('input');
    control.className = 'form-input min-w-0 flex-1';
    control.name = 'f_value';

    if (op === 'expires_in') {
      control.type = 'number';
      control.step = '1';
      control.min = '0';
    } else {
      control.type = 'date';
    }
    return control;
  }

  if (field.field_type === 'enum') {
    // ...

    control = document.createElement('select');
    control.className = 'form-select';
    control.name = 'f_value';

    for (const value of field.enum_values ?? []) {
      control.append(new Option(value, value));
    }

    return control;
  }

  if (field.field_type === 'user') {
    // User filter: free text with datalist suggestions; submits username
    // and the backend resolves it (substring match for "~").
    control = document.createElement('input');
    control.className = 'form-input min-w-0 flex-1';
    control.name = 'f_value';
    control.type = 'text';
    control.placeholder = 'Enter username';
    attachUserDatalist(control);

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
  } else if (field.field_type === 'date' || field.field_type === 'expiry_date') {
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

    let valueControl = buildFilterValueControl(field, opSelect.value);

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

    const refreshValueControl = () => {
      if (field.field_type === 'expiry_date') {
        const newValueControl = buildFilterValueControl(field, opSelect.value);
        let newValueNode = newValueControl;
        if (newValueControl.tagName === 'SELECT') {
          newValueNode = wrapSelectWithChevron(newValueControl);
          newValueNode.classList.add('cf-filter-value-wrap', 'flex-1');
        }
        inputLine.replaceChild(newValueNode, valueNode);
        valueControl = newValueControl;
        valueNode = newValueNode;
      }
    };

    const valueRow = document.createElement('div');

    valueRow.className = 'flex w-full flex-col gap-2';

    valueRow.append(inputLine);

    if (matchCaseLabel) {
      valueRow.append(matchCaseLabel);
    }

    // The value row is hidden while "—" filters for items with no stored
    // value; the hidden sentinel is submitted instead of the value control.
    const applyMode = () => {
      refreshValueControl();
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

    // Only selects get the chevron overlay; text inputs keep the plain
    // form-input look.
    if (valueControl.tagName === 'SELECT') {
      const valueWrap = wrapSelectWithChevron(valueControl);

      valueWrap.classList.add('cf-filter-value-wrap', 'min-w-0', 'flex-1');

      selectsLine.append(valueWrap);
    } else {
      valueControl.classList.add('cf-filter-value', 'min-w-0', 'flex-1');

      selectsLine.append(valueControl);
    }
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
    fieldSelect.append(new Option(field.name, field.id));
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
    const data = await response.json().catch(() => ({}));
    const errorEl = document.getElementById('edit-item-error');
    if (errorEl) {
      errorEl.textContent = data.error || 'Save failed';
      errorEl.classList.remove('hidden');
    }
    editItemForm.reportValidity();
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
const viewItemUpdatedAt = document.getElementById('view-item-updated-at');
const viewItemLocation = document.getElementById('view-item-location');
const viewItemCopy = document.getElementById('view-item-copy');
const viewItemEdit = document.getElementById('view-item-edit');
const viewItemAudit = document.getElementById('view-item-audit');
const viewItemArchived = document.getElementById('view-item-archived');
const viewItemRestore = document.getElementById('view-item-restore');
const viewItemArchivalReasonRow = document.getElementById('view-item-archival-reason-row');
const viewItemArchivalReason = document.getElementById('view-item-archival-reason');
const viewItemArchivalNotesRow = document.getElementById('view-item-archival-notes-row');
const viewItemArchivalNotes = document.getElementById('view-item-archival-notes');

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
    viewItemArchivalReasonRow.classList.toggle('hidden', !isArchived);
    viewItemArchivalNotesRow.classList.toggle('hidden', !isArchived);
    viewItemArchivalReason.textContent = isArchived ? (asset.archival_reason || '—') : '';
    viewItemArchivalNotes.textContent = isArchived ? (asset.archival_notes || '—') : '';

    viewItemId.textContent = asset.id;
    viewItemName.textContent = asset.name;
    viewItemDescription.textContent = asset.description || '—';
    const formatUpdatedAtTimestamps = (timestamp) => {
      const utc = timestamp
      const date = utc ? new Date(utc.replace(' ', 'T') + 'Z') : null;

      if (date && !Number.isNaN(date.getTime())) {
        return date.toLocaleString();
      }

      return '—'; // Return a default value if the date is invalid
    };
    viewItemUpdatedAt.textContent = formatUpdatedAtTimestamps(asset.updated_at); //TODO
    viewItemLocation.textContent = asset.location_name || '—';

    renderViewItemCustomFields(
      await loadCustomFields(),
      asset.custom_fields ?? {}
    );
  });
}


// Handle View Asset.

function handleViewItem(event) {
  if (event.target.closest('.copy-item-id, .edit-item, .restore-item, .view-item-link')) {
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

// View → Audit.

viewItemAudit?.addEventListener('click', () => {
  if (!currentViewItemId) {
    return;
  }

  const auditUrl = new URL(viewItemAudit.dataset.auditBase, window.location.href);
  auditUrl.searchParams.set('entity_id', currentViewItemId);
  window.location.href = auditUrl.toString();
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

  const reasonEl = document.getElementById('archive-item-reason');
  const notesEl = document.getElementById('archive-item-notes');

  if (reasonEl && !reasonEl.value) {
    reasonEl.reportValidity();
    return;
  }

  const body = new FormData();

  if (reasonEl) {
    body.set('archival_reason', reasonEl.value);
  }

  if (notesEl && notesEl.value.trim()) {
    body.set('archival_notes', notesEl.value);
  }

  const response = await fetch(
    `/inventory/${currentEditItemId}/archive`,
    {
      method: 'POST',
      headers: { 'X-CSRF-Token': document.querySelector('input[name="csrf_token"]')?.value ?? '' },
      body
    }
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const errorEl = document.getElementById('archive-item-error');
    if (errorEl) {
      errorEl.textContent = data.error || 'Archive failed';
      errorEl.classList.remove('hidden');
    }
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
      method: 'POST',
      headers: { 'X-CSRF-Token': document.querySelector('input[name="csrf_token"]')?.value ?? '' }
    }
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const errorEl = document.getElementById('restore-item-error');
    if (errorEl) {
      errorEl.textContent = data.error || 'Restore failed';
      errorEl.classList.remove('hidden');
    }
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


// ==================== Filter Persistence ====================

const FILTERS_STORAGE_KEY = 'inventory-filters';

function loadSavedInventoryFilters() {
  try {
    const raw = sessionStorage.getItem(FILTERS_STORAGE_KEY);

    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.error('Failed to load saved inventory filters:', error);
    return null;
  }
}

function saveInventoryFilters() {
  try {
    const params = getInventoryParams();

    sessionStorage.setItem(
      FILTERS_STORAGE_KEY,
      JSON.stringify({
        page: currentInventoryPage,
        search: params.get('search') ?? '',
        include_archived: params.get('include_archived') === 'true',
        sort_by: params.get('sort_by') ?? 'name',
        sort_order: params.get('sort_order') ?? 'asc',
        location_id: params.get('location_id') ?? '',
        f_field: params.getAll('f_field'),
        f_op: params.getAll('f_op'),
        f_value: params.getAll('f_value')
      })
    );
  } catch (error) {
    console.error('Failed to save inventory filters:', error);
  }
}

function clearSavedInventoryFilters() {
  try {
    sessionStorage.removeItem(FILTERS_STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear saved inventory filters:', error);
  }
}

async function applyInventoryFilters(saved) {
  if (!saved) {
    return;
  }

  if (searchInput) {
    searchInput.value = saved.search ?? '';
  }

  if (includeArchived) {
    includeArchived.checked = saved.include_archived === true;
  }

  if (filterLocation && saved.location_id !== undefined && saved.location_id !== '') {
    await loadLocations();
    filterLocation.value = saved.location_id;
  }

  const fields = await loadCustomFields();

  if (filterSortBy) {
    populateFilterSortBy(fields);
    filterSortBy.value = saved.sort_by ?? 'name';
  }

  const sortOrder = document.querySelector(
    `input[name="sort_order"][value="${saved.sort_order === 'desc' ? 'desc' : 'asc'}"]`
  );

  if (sortOrder) {
    sortOrder.checked = true;
  }

  if (!customFieldFilterRows || (saved.f_field ?? []).length === 0) {
    return;
  }

  // Rebuild the custom-field filter rows from the saved triplets. Rows for
  // fields that no longer exist are skipped.
  for (let index = 0; index < saved.f_field.length; index++) {
    const fieldId = saved.f_field[index];

    if (!fields.some((field) => String(field.id) === String(fieldId))) {
      continue;
    }

    const row = buildFilterRow(fields);
    const fieldSelect = row.querySelector('.cf-filter-field');

    fieldSelect.value = String(fieldId);
    fieldSelect.dispatchEvent(new Event('change'));

    const opSelect = row.querySelector('.cf-filter-op');

    if (opSelect && saved.f_op[index]) {
      const isKnown = [...opSelect.options].some(
        (option) => option.value === saved.f_op[index]
      );

      if (isKnown) {
        opSelect.value = saved.f_op[index];
        opSelect.dispatchEvent(new Event('change'));
      }
    }

    // The first (non-hidden) control holds the real value; the hidden
    // sentinel backstops the "no stored value" operator.
    const valueControl = row.querySelector('[name="f_value"]');

    if (valueControl && valueControl.type !== 'hidden') {
      valueControl.value = saved.f_value[index] ?? '';
    }

    customFieldFilterRows.append(row);
  }
}

// ==================== End Filter Persistence ====================


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

  clearSavedInventoryFilters();
}

// Restore saved filters on refresh, otherwise start with defaults.

(async () => {
  const saved = loadSavedInventoryFilters();

  if (saved) {
    await applyInventoryFilters(saved);
    loadInventory(saved.page ?? 1);
  } else {
    resetInventoryFilters();
    loadInventory();
  }
})();

// ==================== End Initial Load ====================
