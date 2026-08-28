const addItemModal = document.getElementById("add-item-modal");

const openAddItemButtons = [
  document.getElementById("add-item-button"),
  document.getElementById("empty-add-item-button")
];

const closeAddItemButtons = [
  document.getElementById("close-add-item-modal"),
  document.getElementById("cancel-add-item")
];

for (const button of openAddItemButtons) {
  button?.addEventListener("click", () => {
    addItemModal?.showModal();
  });
}

for (const button of closeAddItemButtons) {
  button?.addEventListener("click", () => {
    addItemModal?.close();
  });
}

addItemModal?.addEventListener("click", (event) => {
  if (event.target === addItemModal) {
    addItemModal.close();
  }
});

for (const button of document.querySelectorAll(".copy-item-id")) {
  button.addEventListener("click", async () => {
    const itemId = button.dataset.itemId;

    if (!itemId) {
      return;
    }

    await navigator.clipboard.writeText(itemId);

    const icon = button.querySelector("i");

    if (!icon) {
      return;
    }

    icon.classList.remove("bi-copy");
    icon.classList.add("bi-check");

    setTimeout(() => {
      icon.classList.remove("bi-check");
      icon.classList.add("bi-copy");
    }, 1500);
  });
}

const editItemModal = document.getElementById("edit-item-modal");
const editItemForm = document.getElementById("edit-item-form");
const editItemName = document.getElementById("edit-item-name");
const editItemLocation = document.getElementById("edit-item-location");

for (const button of document.querySelectorAll(".edit-item")) {
  button.addEventListener("click", async () => {
    const itemId = button.dataset.itemId;

    if (!itemId) {
      return;
    }

    const response = await fetch(`/inventory/${itemId}`);

    if (!response.ok) {
      return;
    }

    const item = await response.json();

    editItemName.value = item.name;
    editItemLocation.value = item.location_id ?? "";
    editItemForm.action = `/inventory/${itemId}`;

    editItemModal.showModal();
  });
}

for (const button of [
  document.getElementById("close-edit-item-modal"),
  document.getElementById("cancel-edit-item")
]) {
  button?.addEventListener("click", () => {
    editItemModal?.close();
  });
}

editItemModal?.addEventListener("click", (event) => {
  if (event.target === editItemModal) {
    editItemModal.close();
  }
});
