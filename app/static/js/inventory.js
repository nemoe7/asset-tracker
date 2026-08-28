// ==================== Live Search ====================

const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search');

let searchTimeout = null;


// Submit search after the user stops typing.
searchInput?.addEventListener('input', () => {
  clearTimeout(searchTimeout);

  searchTimeout = setTimeout(() => {
    searchForm?.requestSubmit();
  }, 300);
});


// Keep focus on the search input when a search is active.
if (searchInput?.value) {
  searchInput.focus();
  searchInput.setSelectionRange(
    searchInput.value.length,
    searchInput.value.length
  );
}

// ==================== End Live Search ====================

// ==================== Filter & Sort Modal ====================

const filterItemModal = document.getElementById('filter-item-modal');
const filterItemForm = document.getElementById('filter-item-form');
const filterItemButton = document.getElementById('filter-item-button');
const closeFilterItemModal = document.getElementById('close-filter-item-modal');
const clearFilterItemButton = document.getElementById('clear-filter-item');


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


// Clear all filters and sorting options.
clearFilterItemButton?.addEventListener('click', () => {
  filterItemForm?.querySelectorAll('input[type="checkbox"]').forEach((input) => {
    input.checked = false;
  });

  const ascendingOption = filterItemForm?.querySelector(
    'input[name="sort_order"][value="asc"]'
  );

  if (ascendingOption) {
    ascendingOption.checked = true;
  }

  const sortBy = document.getElementById('filter-sort-by');

  if (sortBy) {
    sortBy.value = 'name';
  }
});


// ==================== End Filter & Sort Modal ====================

// ==================== Add Item Modal ====================

const addItemModal = document.getElementById('add-item-modal');

const openAddItemButtons = [
  document.getElementById('add-item-button'),
  document.getElementById('empty-add-item-button')
];

const closeAddItemButtons = [
  document.getElementById('close-add-item-modal'),
  document.getElementById('cancel-add-item')
];


// ==================== Open Add Item Modal ====================

for (const button of openAddItemButtons) {
  button?.addEventListener('click', () => {
    addItemModal?.showModal();
  });
}

// ==================== End Open Add Item Modal ====================


// ==================== Close Add Item Modal ====================

for (const button of closeAddItemButtons) {
  button?.addEventListener('click', () => {
    addItemModal?.close();
  });
}

addItemModal?.addEventListener('click', (event) => {
  if (event.target === addItemModal) {
    addItemModal.close();
  }
});

// ==================== End Close Add Item Modal ====================


// ==================== Copy Asset ID ====================

for (const button of document.querySelectorAll('.copy-item-id')) {
  button.addEventListener('click', async () => {
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
  });
}

// ==================== End Copy Asset ID ====================


// ==================== Edit Asset Modal ====================

const editItemModal = document.getElementById('edit-item-modal');
const editItemLoading = document.getElementById('edit-item-loading');
const editItemForm = document.getElementById('edit-item-form');

const editItemId = document.getElementById('edit-item-id');
const editItemName = document.getElementById('edit-item-name');
const editItemLocation = document.getElementById('edit-item-location');

let currentEditItemId = null;


// ==================== Open Edit Asset Modal ====================

for (const button of document.querySelectorAll('.edit-item')) {
  button.addEventListener('click', async () => {
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
  });
}

// ==================== End Open Edit Asset Modal ====================


// ==================== Close Edit Asset Modal ====================

document
  .getElementById('close-edit-item-modal')
  ?.addEventListener('click', () => {
    editItemModal?.close();
  });

editItemModal?.addEventListener('click', (event) => {
  if (event.target === editItemModal) {
    editItemModal.close();
  }
});

// ==================== End Close Edit Asset Modal ====================


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


// ==================== Open View Asset Modal ====================

for (const item of document.querySelectorAll('.view-item')) {
  item.addEventListener('click', async (event) => {

    // Action buttons have their own click handlers.
    if (event.target.closest('.copy-item-id, .edit-item')) {
      return;
    }

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
  });
}

// ==================== End Open View Asset Modal ====================


// ==================== Copy Asset ID from View Asset ====================

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

// ==================== End Copy Asset ID from View Asset ====================


// ==================== Close View Asset Modal ====================

document
  .getElementById('close-view-item-modal')
  ?.addEventListener('click', () => {
    viewItemModal?.close();
  });

viewItemModal?.addEventListener('click', (event) => {
  if (event.target === viewItemModal) {
    viewItemModal.close();
  }
});

// ==================== End Close View Asset Modal ====================


// ==================== View → Edit ====================

viewItemEdit?.addEventListener('click', () => {
  if (!currentViewItemId) {
    return;
  }

  viewItemModal?.close();

  const editButton = document.querySelector(
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


// ==================== Open Archive Confirmation ====================

archiveItemButton?.addEventListener('click', () => {
  if (!currentEditItemId) {
    return;
  }

  archiveItemModal?.showModal();
});

// ==================== End Open Archive Confirmation ====================


// ==================== Cancel Archive ====================

cancelArchiveItem?.addEventListener('click', () => {
  archiveItemModal?.close();
});

// ==================== End Cancel Archive ====================


// ==================== Confirm Archive ====================

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

  window.location.reload();
});

// ==================== End Confirm Archive ====================


// ==================== Close Archive Confirmation ====================

archiveItemModal?.addEventListener('click', (event) => {
  if (event.target === archiveItemModal) {
    archiveItemModal.close();
  }
});

// ==================== End Close Archive Confirmation ====================


// ==================== End Archive Asset ====================
