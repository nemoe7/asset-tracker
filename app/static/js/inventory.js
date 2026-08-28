// ==================== Inventory List ====================

const inventoryContent = document.getElementById('inventory-content');
const inventoryLoading = document.getElementById('inventory-loading');
const searchInput = document.getElementById('search');
const filterForm = document.getElementById('filter-item-form');
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
  icon.classList.add('bi-clipboard-check');

  setTimeout(() => {
    icon.classList.remove('bi-clipboard-check');
    icon.classList.add('bi-copy');
  }, 1500);
}


// ==================== End Copy Asset ID ====================


// ==================== Filter & Sort Modal ====================

const filterItemButton = document.getElementById('filter-item-button');
const filterItemModal = document.getElementById('filter-item-modal');
const closeFilterItemModal = document.getElementById('close-filter-item-modal');
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
  filterItemModal?.showModal();
});


// Close Filter & Sort modal.
closeFilterItemModal?.addEventListener('click', () => {
  filterItemModal?.close();
});


// Close Filter & Sort modal when clicking the backdrop.
filterItemModal?.addEventListener('click', (event) => {
  if (event.target === filterItemModal) {
    filterItemModal.close();
  }
});


// Clear filters.
clearFilterItem?.addEventListener('click', () => {
  filterForm?.reset();
  resetInventoryFilters();
  loadInventory(1);
  filterItemModal?.close();
});


// Apply filters without navigating.
filterForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  loadInventory(1);
  filterItemModal?.close();
});


// ==================== End Filter & Sort Modal ====================


// ==================== Add Item Modal ====================

const addItemModal = document.getElementById('add-item-modal');

const openAddItemButtons = [
  document.getElementById('add-item-button')
];


// Open dynamically loaded Add Item button.
document.addEventListener('click', (event) => {
  if (event.target.closest('#empty-add-item-button')) {
    addItemModal?.showModal();
  }
});


// Open Add Item modal.
for (const button of openAddItemButtons) {
  button?.addEventListener('click', () => {
    addItemModal?.showModal();
  });
}


// Close Add Item modal.
const closeAddItemButtons = [
  document.getElementById('close-add-item-modal'),
  document.getElementById('cancel-add-item')
];

for (const button of closeAddItemButtons) {
  button?.addEventListener('click', () => {
    addItemModal?.close();
  });
}


// Close Add Item modal when clicking the backdrop.
addItemModal?.addEventListener('click', (event) => {
  if (event.target === addItemModal) {
    addItemModal.close();
  }
});


// ==================== End Add Item Modal ====================


// ==================== Edit Asset Modal ====================

const editItemModal = document.getElementById('edit-item-modal');
const editItemLoading = document.getElementById('edit-item-loading');
const editItemForm = document.getElementById('edit-item-form');

const editItemId = document.getElementById('edit-item-id');
const editItemName = document.getElementById('edit-item-name');

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

  editItemLoading?.classList.remove('hidden');
  editItemForm?.classList.add('hidden');

  editItemModal?.showModal();

  const response = await fetch(`/inventory/${itemId}`);

  if (!response.ok) {
    editItemModal?.close();
    return;
  }

  const item = await response.json();

  await loadLocations();

  editItemId.textContent = item.id;
  editItemName.value = item.name;
  editItemLocation.value = item.location_id ?? '';
  editItemForm.action = `/inventory/${itemId}`;

  editItemLoading?.classList.add('hidden');
  editItemForm?.classList.remove('hidden');
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

  editItemModal?.close();
  loadInventory(currentInventoryPage);
});


// Close Edit Asset modal.
document
  .getElementById('close-edit-item-modal')
  ?.addEventListener('click', () => {
    editItemModal?.close();
  });


// Close Edit Asset modal when clicking the backdrop.
editItemModal?.addEventListener('click', (event) => {
  if (event.target === editItemModal) {
    editItemModal.close();
  }
});


// ==================== End Edit Asset Modal ====================


// ==================== View Asset Modal ====================

const viewItemModal = document.getElementById('view-item-modal');
const viewItemLoading = document.getElementById('view-item-loading');
const viewItemContent = document.getElementById('view-item-content');

const viewItemId = document.getElementById('view-item-id');
const viewItemName = document.getElementById('view-item-name');
const viewItemLocation = document.getElementById('view-item-location');
const viewItemCopy = document.getElementById('view-item-copy');
const viewItemEdit = document.getElementById('view-item-edit');
const viewItemArchived = document.getElementById("view-item-archived");

let currentViewItemId = null;


// Handle View Asset.
async function handleViewItem(event) {
  if (event.target.closest('.copy-item-id, .edit-item')) {
    return;
  }

  const item = event.currentTarget;
  const itemId = item.dataset.itemId;

  if (!itemId) {
    return;
  }

  currentViewItemId = itemId;

  viewItemLoading?.classList.remove('hidden');
  viewItemContent?.classList.add('hidden');

  viewItemModal?.showModal();

  const response = await fetch(
    `/inventory/${itemId}?include_archived=true`
  );

  if (!response.ok) {
    viewItemModal?.close();
    return;
  }

  const asset = await response.json();

  viewItemId.textContent = asset.id;
  viewItemArchived.classList.toggle(
    'hidden',
    !asset.archived_at
  );
  viewItemName.textContent = asset.name;
  viewItemLocation.textContent = asset.location_name || '—';

  viewItemLoading?.classList.add('hidden');
  viewItemContent?.classList.remove('hidden');
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
  icon.classList.add('bi-clipboard-check');

  setTimeout(() => {
    icon.classList.remove('bi-clipboard-check');
    icon.classList.add('bi-copy');
  }, 1500);
});


// Close View Asset modal.
document
  .getElementById('close-view-item-modal')
  ?.addEventListener('click', () => {
    viewItemModal?.close();
  });


// Close View Asset modal when clicking the backdrop.
viewItemModal?.addEventListener('click', (event) => {
  if (event.target === viewItemModal) {
    viewItemModal.close();
  }
});


// ==================== End View Asset Modal ====================


// ==================== View → Edit ====================

viewItemEdit?.addEventListener('click', () => {
  if (!currentViewItemId) {
    return;
  }

  viewItemModal?.close();

  const editButton = inventoryContent?.querySelector(
    `.edit-item[data-item-id="${CSS.escape(currentViewItemId)}"]`
  );

  editButton?.click();
});


// ==================== End View → Edit ====================


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

  archiveItemModal?.showModal();
});


// Cancel Archive.
cancelArchiveItem?.addEventListener('click', () => {
  archiveItemModal?.close();
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
    archiveItemModal?.close();
    return;
  }

  archiveItemModal?.close();
  editItemModal?.close();

  loadInventory(currentInventoryPage);
});


// Close Archive confirmation when clicking the backdrop.
archiveItemModal?.addEventListener('click', (event) => {
  if (event.target === archiveItemModal) {
    archiveItemModal.close();
  }
});


// ==================== End Archive Asset ====================


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
