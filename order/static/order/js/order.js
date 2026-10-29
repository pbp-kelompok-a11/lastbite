(() => {
  function showImageFallback(img) {
    if (!img.matches('.order-product__photo')) return;
    img.hidden = true;
    const fallback = img.parentElement.querySelector('.order-image-fallback');
    if (fallback) fallback.hidden = false;
  }
  document.addEventListener('error', event => {
    if (event.target instanceof HTMLImageElement) showImageFallback(event.target);
  }, true);
  function checkImages() {
    document.querySelectorAll('.order-product__photo').forEach(img => {
      if (img.complete && !img.naturalWidth) showImageFallback(img);
    });
  }
  checkImages();

  const reservation = document.getElementById('reservation-form');
  if (reservation) {
    const quantity = reservation.querySelector('[name="quantity"]');
    const total = document.getElementById('reservation-total');
    const unitPrice = Number(reservation.dataset.unitPrice);
    const currency = new Intl.NumberFormat('id-ID', {style: 'currency', currency: 'IDR', maximumFractionDigits: 0});
    const updateTotal = () => {
      const amount = Number(quantity.value);
      total.textContent = quantity.value && Number.isInteger(amount) && quantity.validity.valid
        ? currency.format(unitPrice * amount) : 'Periksa jumlah paket';
    };
    quantity.addEventListener('input', updateTotal);
    updateTotal();
  }

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
  const pickupDialog = document.getElementById('pickup-dialog');
  let selectedTab = page.dataset.tab;
  let pending = false;
  let refreshSequence = 0;

  function showNotice(message, failed = false) {
    notice.textContent = message;
    notice.dataset.error = String(failed);
    notice.hidden = false;
  }
  async function refresh() {
    const sequence = ++refreshSequence;
    const url = new URL(page.dataset.listUrl, location.origin);
    url.searchParams.set('status', filter.value);
    url.searchParams.set('tab', selectedTab);
    cards.setAttribute('aria-busy', 'true');
    try {
      const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store'});
      if (!response.ok || response.redirected) throw new Error('Daftar belum dapat diperbarui. Periksa koneksi dan sesi loginmu.');
      const data = await response.json();
      if (sequence !== refreshSequence) return;
      const expanded = [...cards.querySelectorAll('[data-order-id]')].map(card => ({
        id: card.dataset.orderId, open: card.open, detailOpen: Boolean(card.querySelector('.order-details[open]')),
      }));
      cards.innerHTML = data.html;
      expanded.forEach(item => {
        const card = cards.querySelector(`[data-order-id="${CSS.escape(item.id)}"]`);
        if (!card) return;
        if (item.open && card instanceof HTMLDetailsElement) card.open = true;
        if (item.detailOpen) card.querySelector('.order-details')?.setAttribute('open', '');
      });
      checkImages();
      page.dataset.tab = data.tab;
      selectedTab = data.tab;
      document.getElementById('active-count').textContent = data.active_count;
      document.getElementById('history-count').textContent = data.history_count;
      document.getElementById('filter-tab').value = data.tab;
      filter.replaceChildren(new Option('Semua status', ''));
      data.statuses.forEach(([value, label]) => filter.add(new Option(label, value)));
      filter.value = data.selected_status;
      document.querySelectorAll('[data-order-tab]').forEach(link => {
        const active = link.dataset.orderTab === data.tab;
        link.classList.toggle('is-active', active);
        if (active) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
      });
      const currentUrl = new URL(location.href);
      currentUrl.searchParams.set('tab', data.tab);
      if (data.selected_status) currentUrl.searchParams.set('status', data.selected_status);
      else currentUrl.searchParams.delete('status');
      window.history.replaceState(null, '', currentUrl);
    } finally {
      if (sequence === refreshSequence) cards.setAttribute('aria-busy', 'false');
    }
  }
  const refreshWithNotice = () => refresh().catch(e => {
    selectedTab = page.dataset.tab;
    showNotice(e.message, true);
  });
  filter.addEventListener('change', () => {
    document.querySelector('.order-filter').open = false;
    refreshWithNotice();
  });
  document.getElementById('orders-refresh').addEventListener('click', refreshWithNotice);
  document.querySelectorAll('[data-order-tab]').forEach(link => link.addEventListener('click', event => {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    selectedTab = link.dataset.orderTab;
    filter.value = '';
    refreshWithNotice();
  }));
  document.getElementById('pickup-dialog-close')?.addEventListener('click', () => pickupDialog.close());
  pickupDialog?.addEventListener('close', () => { document.getElementById('pickup-display').textContent = ''; });
  cards.addEventListener('click', event => {
    const pickup = event.target.closest('[data-pickup-code]');
    if (pickup && pickupDialog) {
      document.getElementById('pickup-display').textContent = pickup.dataset.pickupCode;
      document.getElementById('pickup-dialog-name').textContent = pickup.dataset.pickupName;
      pickupDialog.showModal();
      return;
    }
    const button = event.target.closest('[data-order-action]');
    if (!button || pending) return;
    const descriptions = {
      cancel: ['Batalkan pesanan?', 'Stok akan dikembalikan. Pesanan hanya dapat dibatalkan saat masih Pending.'],
      ready: ['Paket siap diambil?', 'Pastikan paket sudah disiapkan sebelum memberi tahu customer.'],
      complete: ['Verifikasi serah terima', 'Cocokkan kode pickup customer sebelum menyerahkan makanan dan menyelesaikan pesanan.'],
    };
    const action = button.dataset.orderAction;
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
      const response = await fetch(form.action, {method: 'POST', body: new FormData(form), credentials: 'same-origin', mode: 'same-origin'});
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
  window.setInterval(() => {
    if (!document.hidden && !dialog.open && !pickupDialog?.open && !pending) refreshWithNotice();
  }, 15000);
})();
