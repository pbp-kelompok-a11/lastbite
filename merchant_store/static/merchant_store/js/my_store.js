// Dialog konfirmasi hapus toko
(() => {
  const dialog = document.getElementById('ms-delete-dialog');
  const openButton = document.getElementById('ms-delete-open');
  const cancelButton = document.getElementById('ms-delete-cancel');
  if (!dialog || !openButton || !cancelButton) return;

  openButton.addEventListener('click', () => dialog.showModal());
  cancelButton.addEventListener('click', () => dialog.close());
})();
