// ==================== Modal Manager ====================

const modalManager = document.getElementById('modal-manager');
const modalManagerContent = document.getElementById('modal-manager-content');
const modalManagerLoading = document.getElementById('modal-manager-loading');

let activeModal = null;
let activeModalParent = null;
let activeModalNextSibling = null;
let modalCloseHandler = null;

modalManager?.addEventListener('cancel', (event) => {
  event.preventDefault();
  closeModal();
});

document.addEventListener('click', (event) => {
  if (event.target.closest('.modal-close')) {
    closeModal();
  }
});

// Register an async handler run before the modal manager closes.

function onModalClose(handler) {
  modalCloseHandler = handler;
}

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
  if (modalCloseHandler) {
    await modalCloseHandler();
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
