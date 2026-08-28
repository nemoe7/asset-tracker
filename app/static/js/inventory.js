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


// Open Add Item modal.
for (const button of openAddItemButtons) {
  button?.addEventListener('click', () => {
    addItemModal?.showModal();
  });
}


// Close Add Item modal.
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
    icon.classList.add('bi-clipboard-check');

    setTimeout(() => {
      icon.classList.remove('bi-clipboard-check');
      icon.classList.add('bi-copy');
    }, 1500);
  });
}


// ==================== Edit Asset Modal ====================

const editItemModal = document.getElementById('edit-item-modal');
const editItemLoading = document.getElementById('edit-item-loading');
const editItemForm = document.getElementById('edit-item-form');

const editItemId = document.getElementById('edit-item-id');
const editItemName = document.getElementById('edit-item-name');
const editItemLocation = document.getElementById('edit-item-location');


// Open Edit Asset modal immediately, then load current asset data.
for (const button of document.querySelectorAll('.edit-item')) {
  button.addEventListener('click', async () => {
    const itemId = button.dataset.itemId;

    if (!itemId) {
      return;
    }

    editItemLoading?.classList.remove('hidden');
    editItemForm?.classList.add('hidden');

    editItemModal?.showModal();

    const response = await fetch(`/inventory/${itemId}`);

    if (!response.ok) {
      editItemModal?.close();
      return;
    }

    const item = await response.json();

    // Populate the current asset data.
    editItemId.textContent = item.id;
    editItemName.value = item.name;
    editItemLocation.value = item.location_id ?? '';
    editItemForm.action = `/inventory/${itemId}`;

    // Replace loading state with the form.
    editItemLoading?.classList.add('hidden');
    editItemForm?.classList.remove('hidden');
  });
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


// ==================== View Asset Modal ====================

const viewItemModal = document.getElementById('view-item-modal');
const viewItemLoading = document.getElementById('view-item-loading');
const viewItemContent = document.getElementById('view-item-content');

const viewItemId = document.getElementById('view-item-id');
const viewItemName = document.getElementById('view-item-name');
const viewItemLocation = document.getElementById('view-item-location');

const viewItemEdit = document.getElementById('view-item-edit');

let currentViewItemId = null;


// Open View Asset modal immediately, then load current asset data.
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

    // Show loading state immediately.
    viewItemLoading?.classList.remove('hidden');
    viewItemContent?.classList.add('hidden');

    viewItemModal?.showModal();

    const response = await fetch(`/inventory/${itemId}`);

    if (!response.ok) {
      viewItemModal?.close();
      return;
    }

    const asset = await response.json();

    // Populate the current asset data.
    viewItemId.textContent = asset.id;
    viewItemName.textContent = asset.name;
    viewItemLocation.textContent = asset.location_name || 'No location';

    // Replace loading state with the asset details.
    viewItemLoading?.classList.add('hidden');
    viewItemContent?.classList.remove('hidden');
  });
}


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


// ==================== View → Edit ====================

// Open the existing Edit Asset modal from View Asset.
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
