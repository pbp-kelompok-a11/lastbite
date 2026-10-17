const logoutDialog = document.getElementById('logout-dialog');
const logoutOpen = document.getElementById('logout-open');
const logoutCancel = document.getElementById('logout-cancel');
const logoutForm = document.getElementById('logout-form');

if (logoutDialog && logoutOpen && logoutCancel && logoutForm) {
  const submitButton = document.getElementById('logout-submit');
  const errorMessage = document.getElementById('logout-error');
  let pending = false;

  logoutOpen.addEventListener('click', () => {
    errorMessage.hidden = true;
    logoutDialog.showModal();
  });
  logoutCancel.addEventListener('click', () => logoutDialog.close());
  logoutDialog.addEventListener('cancel', (event) => {
    if (pending) event.preventDefault();
  });

  logoutForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (pending) return;
    pending = true;
    submitButton.disabled = true;
    logoutCancel.disabled = true;
    submitButton.textContent = 'Sedang logout…';
    errorMessage.hidden = true;
    try {
      const response = await fetch(logoutForm.action, {
        method: 'POST',
        body: new FormData(logoutForm),
        credentials: 'same-origin',
        mode: 'same-origin',
      });
      if (!response.ok || !response.redirected) throw new Error('Logout failed');
      window.location.assign(logoutForm.dataset.successUrl);
    } catch {
      errorMessage.textContent = 'Logout belum dapat dikonfirmasi. Coba lagi atau muat ulang halaman.';
      errorMessage.hidden = false;
      pending = false;
      submitButton.disabled = false;
      logoutCancel.disabled = false;
      submitButton.textContent = 'Ya, logout';
    }
  });
}
