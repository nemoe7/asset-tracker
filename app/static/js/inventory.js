// ==================== Inventory List ====================

const inventoryContent = document.getElementById('inventory-content');
const inventoryLoading = document.getElementById('inventory-loading');
const searchInput = document.getElementById('search');
const filterForm = document.getElementById('filter-item-form');

let inventorySearchTimeout = null;
let inventoryRequest = null;
let currentInventoryPage = 1;


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

  try {
    const response = await fetch(
      `/inventory/fragment?${params.toString()}`,
      {
        signal: inventoryRequest.signal
      }
    );

    if (!response.ok) {
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

const filterItemModal = document.getElementById('filter-item-modal');
const filterItemButton = document.getElementById('filter-item-button');
const closeFilterItemModal = document.getElementById(
  'close-filter-item-modal'
);
const clearFilterItem = document.getElementById('clear-filter-item');


// Open Filter & Sort modal.
filterItemButton?.addEventListener('click', () => {
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


// Clear Filter & Sort options.
clearFilterItem?.addEventListener('click', () => {
  filterForm?.reset();
  filterItemModal?.close();
  loadInventory(1);
});


// Apply Filter & Sort options.
filterForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  filterItemModal?.close();
  loadInventory(1);
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
const editItemLocation = document.getElementById('edit-item-location');

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

  editItemId.textContent = item.id;
  editItemName.value = item.name;
  editItemLocation.value = item.location_id ?? '';
  editItemForm.action = `/inventory/${itemId}`;

  editItemLoading?.classList.add('hidden');
  editItemForm?.classList.remove('hidden');
}


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

  const response = await fetch(`/inventory/${itemId}`);

  if (!response.ok) {
    viewItemModal?.close();
    return;
  }

  const asset = await response.json();

  viewItemId.textContent = asset.id;
  viewItemName.textContent = asset.name;
  viewItemLocation.textContent = asset.location_name || 'No location';

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

loadInventory();


// ==================== End Initial Load ====================
