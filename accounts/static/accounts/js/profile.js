document.querySelectorAll('[data-profile-open]').forEach((button) => {
  button.addEventListener('click', () => {
    document.getElementById(button.dataset.profileOpen).showModal();
  });
});

document.querySelectorAll('.profile-dialog').forEach((dialog) => {
  dialog.querySelector('[data-profile-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    dialog.querySelectorAll('input[type="password"]').forEach((input) => {
      input.value = '';
    });
  });
});

document.querySelector('.profile-dialog[data-reopen]')?.showModal();
