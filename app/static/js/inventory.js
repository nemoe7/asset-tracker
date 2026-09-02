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


// ==================== Modal Manager ====================

const modalManager = document.getElementById('modal-manager');
const modalManagerContent = document.getElementById('modal-manager-content');
const modalManagerLoading = document.getElementById('modal-manager-loading');

let activeModal = null;
let activeModalParent = null;
let activeModalNextSibling = null;

modalManager?.addEventListener('cancel', (event) => {
  event.preventDefault();
  closeModal();
});

document.addEventListener('click', (event) => {
  if (event.target.closest('.modal-close')) {
    closeModal();
  }
});

async function openModal(modal, load = null) {
  if (!modal || !modalManager || !modalManagerContent) {
    return;
  }

  if (activeModal === modal) {
    return;
  }

  if (activeModal) {
    closeModalContent();
  }

  activeModal = modal;
  activeModalParent = modal.parentElement;
  activeModalNextSibling = modal.nextSibling;

  modalManagerContent.appendChild(modal);

  modal.classList.add('hidden');
  modalManagerLoading?.classList.toggle('hidden', !load);

  if (!modalManager.open) {
    modalManager.showModal();
  }

  try {
    if (load) {
      await load();
    }
  } finally {
    modalManagerLoading?.classList.add('hidden');

    if (activeModal === modal) {
      modal.classList.remove('hidden');
    }
  }
}

function closeModalContent() {
  if (!activeModal || !activeModalParent) {
    return;
  }

  activeModal.classList.add('hidden');

  if (activeModalNextSibling) {
    activeModalParent.insertBefore(activeModal, activeModalNextSibling);
  } else {
    activeModalParent.appendChild(activeModal);
  }

  activeModal = null;
  activeModalParent = null;
  activeModalNextSibling = null;
}

async function closeModal() {
  if (qrScannerRunning) {
    await stopQrScanner();
  }

  closeModalContent();

  if (modalManager?.open) {
    modalManager.close();
  }
}

function switchModal(modal) {
  if (!modal) {
    return;
  }

  if (!activeModal) {
    openModal(modal);
    return;
  }

  closeModalContent();
  openModal(modal);
}

let isBackgroundClick = false;

modalManager?.addEventListener('mousedown', (event) => {
  isBackgroundClick = event.target === modalManager;
});

modalManager?.addEventListener('click', (event) => {
  if (isBackgroundClick && event.target === modalManager) {
    closeModal();
  }

  isBackgroundClick = false;
});

// ==================== End Modal Manager ====================


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
  openModal(filterItemModal);
});


// Clear filters.

clearFilterItem?.addEventListener('click', () => {
  filterForm?.reset();
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
    openModal(addItemModal);
  }
});


// Open Add Item modal.

document
  .getElementById('add-item-button')
  ?.addEventListener('click', () => {
    loadLocations();
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


// Handle Edit Asset.

async function handleEditItem(event) {
  event.stopPropagation();

  const button = event.currentTarget;
  const itemId = button.dataset.itemId;

  if (!itemId) {
    return;
  }

  currentEditItemId = itemId;

  openModal(editItemModal, async () => {
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
  });
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

  const itemId = currentViewItemId;

  closeModal();

  const editButton = inventoryContent?.querySelector(
    `.edit-item[data-item-id="${CSS.escape(itemId)}"]`
  );

  editButton?.click();
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


// ==================== Manage Locations ====================

const manageLocationsButtons = document.querySelectorAll('.manage-locations-button');
const manageLocationsModal = document.getElementById('manage-locations-modal');
const manageLocationsError = document.getElementById('manage-locations-error');
const manageLocationsList = document.getElementById('manage-locations-list');

const addLocationForm = document.getElementById('add-location-form');

const deleteLocationModal = document.getElementById('delete-location-modal');
const deleteLocationName = document.getElementById('delete-location-name');
const cancelDeleteLocation = document.getElementById('cancel-delete-location');
const confirmDeleteLocation = document.getElementById('confirm-delete-location');

let manageLocationsData = [];
let currentDeleteLocationId = null;


// Show a validation error inside the Manage Locations modal.

function showManageLocationsError(message) {
  if (!manageLocationsError) {
    return;
  }

  manageLocationsError.textContent = message;
  manageLocationsError.classList.remove('hidden');
}


function hideManageLocationsError() {
  manageLocationsError?.classList.add('hidden');
}


// Refresh the location list rendered in the Manage Locations modal.

async function refreshManageLocations() {
  const response = await fetch('/locations');

  if (!response.ok) {
    return;
  }

  manageLocationsData = await response.json();
  renderManageLocations();
}


// Build one row of the Manage Locations list.

function buildLocationRow(location) {
  const row = document.createElement('div');
  row.className =
    'flex items-center justify-between gap-3 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2';

  const details = document.createElement('div');
  details.className = 'min-w-0';

  const name = document.createElement('p');
  name.className = 'truncate text-sm font-medium text-zinc-100';
  name.textContent = location.name;

  details.append(name);

  if (location.description) {
    const description = document.createElement('p');
    description.className = 'truncate text-xs text-zinc-400';
    description.textContent = location.description;

    details.append(description);
  }

  const actions = document.createElement('div');
  actions.className = 'flex shrink-0 gap-1';

  const editButton = document.createElement('button');
  editButton.type = 'button';
  editButton.className =
    'rounded-lg px-2 py-1 text-xs font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-zinc-100';
  editButton.textContent = 'Edit';

  editButton.addEventListener('click', () => {
    renderLocationEditRow(row, location);
  });

  const deleteButton = document.createElement('button');
  deleteButton.type = 'button';
  deleteButton.className =
    'rounded-lg px-2 py-1 text-xs font-medium text-red-400 transition hover:bg-red-950 hover:text-red-300';
  deleteButton.textContent = 'Delete';

  deleteButton.addEventListener('click', () => {
    currentDeleteLocationId = location.id;
    deleteLocationName.textContent = location.name;
    openModal(deleteLocationModal);
  });

  actions.append(editButton, deleteButton);
  row.append(details, actions);

  return row;
}

// Replace a row with inline edit inputs.

function renderLocationEditRow(row, location) {
  row.replaceChildren();

  const inputs = document.createElement('div');
  inputs.className = 'min-w-0 flex-1 space-y-2';

  const nameInput = document.createElement('input');
  nameInput.type = 'text';
  nameInput.required = true;
  nameInput.value = location.name;
  nameInput.className = 'form-input !py-1.5 text-sm';

  const descriptionInput = document.createElement('input');
  descriptionInput.type = 'text';
  descriptionInput.value = location.description ?? '';
  descriptionInput.placeholder = 'Description';
  descriptionInput.className = 'form-input !py-1.5 text-xs';

  inputs.append(nameInput, descriptionInput);

  const actions = document.createElement('div');
  actions.className = 'flex shrink-0 gap-1';

  const cancelButton = document.createElement('button');
  cancelButton.type = 'button';
  cancelButton.className =
    'rounded-lg px-2 py-1 text-xs font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-zinc-100';
  cancelButton.textContent = 'Cancel';

  cancelButton.addEventListener('click', () => {
    renderManageLocations();
  });

  const saveButton = document.createElement('button');
  saveButton.type = 'button';
  saveButton.className =
    'rounded-lg bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-900 transition hover:bg-zinc-300';
  saveButton.textContent = 'Save';

  saveButton.addEventListener('click', async () => {
    const name = nameInput.value.trim();

    if (!name) {
      showManageLocationsError('Location name cannot be empty.');
      return;
    }

    const body = new FormData();
    body.set('name', name);
    body.set('description', descriptionInput.value);

    const response = await fetch(`/locations/${location.id}`, {
      method: 'POST',
      body: body,
      headers: {
        Accept: 'application/json'
      }
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      showManageLocationsError(data.error || 'Failed to update location.');
      return;
    }

    hideManageLocationsError();
    await refreshManageLocations();
    await loadLocations();
  });

  actions.append(cancelButton, saveButton);
  row.append(inputs, actions);

  nameInput.focus();
}


// Render the full list from cached data.

function renderManageLocations() {
  if (!manageLocationsList) {
    return;
  }

  manageLocationsList.replaceChildren();

  if (!manageLocationsData.length) {
    const empty = document.createElement('p');
    empty.className = 'py-2 text-sm text-zinc-400';
    empty.textContent = 'No locations yet.';

    manageLocationsList.append(empty);
    return;
  }

  for (const location of manageLocationsData) {
    manageLocationsList.append(buildLocationRow(location));
  }
}


// Open Manage Locations modal.

for (const button of manageLocationsButtons) {
  button.addEventListener('click', () => {
    hideManageLocationsError();
    openModal(manageLocationsModal, refreshManageLocations);
  });
}


// Submit Add Location without leaving the modal.

addLocationForm?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const response = await fetch('/locations', {
    method: 'POST',
    body: new FormData(addLocationForm),
    headers: {
      Accept: 'application/json'
    }
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    showManageLocationsError(data.error || 'Failed to create location.');
    return;
  }

  addLocationForm.reset();
  hideManageLocationsError();
  await refreshManageLocations();
  await loadLocations();
});


// Cancel Delete Location.

cancelDeleteLocation?.addEventListener('click', () => {
  closeModal();
});


// Confirm Delete Location.

confirmDeleteLocation?.addEventListener('click', async () => {
  if (!currentDeleteLocationId) {
    return;
  }

  const body = new FormData();
  body.set('confirm', 'true');

  const response = await fetch(
    `/locations/${currentDeleteLocationId}/delete`,
    {
      method: 'POST',
      body: body,
      headers: {
        Accept: 'application/json'
      }
    }
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    openModal(manageLocationsModal, refreshManageLocations);

    showManageLocationsError(data.error || 'Failed to delete location.');
    return;
  }

  currentDeleteLocationId = null;
  hideManageLocationsError();
  await loadLocations();
  loadInventory(currentInventoryPage);

  openModal(manageLocationsModal, refreshManageLocations);
});

// ==================== End Manage Locations ====================


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
