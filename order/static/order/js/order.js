(() => {
  const page = document.getElementById('order-page');
  if (!page) return;
  const cards = document.getElementById('order-cards');
  const filter = document.getElementById('status-filter');
  const notice = document.getElementById('order-notice');
  const dialog = document.getElementById('order-dialog');
  const form = document.getElementById('order-action-form');
  const confirm = document.getElementById('order-confirm');
  const close = document.getElementById('order-close');
  const error = document.getElementById('order-dialog-error');
  const code = document.getElementById('pickup-code');
  let pending = false;
  let refreshSequence = 0;

  function showNotice(message, failed = false) {
    notice.textContent = message;
    notice.dataset.error = String(failed);
  }
  async function refresh() {
    const sequence = ++refreshSequence;
    const url = new URL(page.dataset.listUrl, location.origin);
    url.searchParams.set('status', filter.value);
    const response = await fetch(url, { credentials: 'same-origin', cache: 'no-store' });
    if (!response.ok || response.redirected) throw new Error('Daftar belum dapat diperbarui. Periksa koneksi dan sesi loginmu.');
    const data = await response.json();
    if (sequence === refreshSequence) cards.innerHTML = data.html;
  }
  const refreshWithNotice = () => refresh().catch(e => showNotice(e.message, true));
  filter.addEventListener('change', refreshWithNotice);
  document.getElementById('orders-refresh').addEventListener('click', refreshWithNotice);
  cards.addEventListener('click', event => {
    const button = event.target.closest('[data-order-action]');
    if (!button || pending) return;
    const action = button.dataset.orderAction;
    const descriptions = {
      cancel: ['Batalkan pesanan?', 'Stok akan dikembalikan. Pesanan hanya dapat dibatalkan saat masih Pending.'],
      ready: ['Paket siap diambil?', 'Pastikan paket sudah disiapkan sebelum memberi tahu customer.'],
      complete: ['Verifikasi serah terima', 'Cocokkan kode pickup customer sebelum menyerahkan makanan dan menyelesaikan pesanan.'],
    };
    document.getElementById('order-dialog-title').textContent = descriptions[action][0];
    document.getElementById('order-dialog-description').textContent = descriptions[action][1];
    form.action = button.dataset.orderUrl;
    code.value = '';
    code.required = action === 'complete';
    document.getElementById('pickup-code-field').hidden = action !== 'complete';
    error.hidden = true;
    dialog.showModal();
    (action === 'complete' ? code : close).focus();
  });
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('cancel', event => { if (pending) event.preventDefault(); });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (pending) return;
    pending = true;
    confirm.disabled = close.disabled = true;
    error.hidden = true;
    try {
      const response = await fetch(form.action, { method: 'POST', body: new FormData(form), credentials: 'same-origin', mode: 'same-origin' });
      if (response.redirected) throw new Error('Sesi login berakhir. Login kembali lalu perbarui daftar.');
      const data = response.headers.get('content-type')?.includes('application/json') ? await response.json() : {};
      if (!response.ok) throw new Error(data.error || 'Aksi belum berhasil. Periksa akses dan perbarui daftar pesanan.');
      dialog.close();
      showNotice(data.message);
      try { await refresh(); } catch { showNotice('Status tersimpan. Daftar belum diperbarui, tekan Perbarui untuk melihatnya.', true); }
    } catch (e) {
      error.textContent = e.message;
      error.hidden = false;
    } finally {
      pending = false;
      confirm.disabled = close.disabled = false;
    }
  });
  window.setInterval(() => { if (!document.hidden && !dialog.open && !pending) refreshWithNotice(); }, 15000);
})();
