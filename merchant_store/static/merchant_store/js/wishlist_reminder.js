// Pengingat wishlist: simpan pengaturan ke server + notifikasi browser menjelang jam pickup.
(() => {
  const box = document.getElementById('mw-reminder');
  const btn = document.getElementById('mw-reminder-btn');
  const desc = document.getElementById('mw-reminder-desc');
  const toast = document.getElementById('mw-toast');
  const page = document.querySelector('[data-csrf]');
  if (!box || !btn || !page) return;

  const DEFAULT_DESC = 'Stok berubah cepat menjelang jam pickup.';
  const CHECK_EVERY_MS = 30 * 1000;
  let enabled = box.dataset.enabled === 'true';
  let lead = parseInt(box.dataset.lead, 10) || 30;
  let timer = null;
  let toastTimer = null;

  let items = [];
  try {
    items = JSON.parse(document.getElementById('mw-reminder-items').textContent) || [];
  } catch (e) { items = []; }

  const canNotify = 'Notification' in window;

  function showToast(message) {
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 4000);
  }

  function leadLabel() {
    return lead >= 60 ? `${lead / 60} jam` : `${lead} menit`;
  }

  function render() {
    btn.textContent = enabled ? 'Pengingat aktif ✓' : 'Aktifkan pengingat';
    btn.setAttribute('aria-pressed', enabled ? 'true' : 'false');
    desc.textContent = enabled
      ? `Kami ingatkan ${leadLabel()} sebelum jam pickup (selama halaman ini terbuka).`
      : DEFAULT_DESC;
  }

  function minutesUntil(hhmm) {
    const [h, m] = hhmm.split(':').map(Number);
    const now = new Date();
    const target = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, 0);
    return (target - now) / 60000;
  }

  function alreadySent(key) {
    try { return localStorage.getItem(key) === '1'; } catch (e) { return false; }
  }
  function markSent(key) {
    try { localStorage.setItem(key, '1'); } catch (e) { /* abaikan */ }
  }

  function notify(item) {
    const label = item.kind === 'bag' ? 'Pickup' : 'Toko buka';
    const body = item.kind === 'bag'
      ? `${item.name} (${item.store}) mulai bisa diambil pukul ${item.start}. Sisa ${item.stock} bag.`
      : `${item.name} buka pukul ${item.start}.`;
    const title = `${label} segera dimulai`;

    if (canNotify && Notification.permission === 'granted') {
      const n = new Notification(title, { body, tag: `${item.kind}-${item.id}` });
      n.onclick = () => { window.focus(); window.location.href = item.url; n.close(); };
    } else {
      showToast(`${title}: ${body}`);
    }
  }

  function check() {
    if (!enabled) return;
    const today = new Date().toISOString().slice(0, 10);
    items.forEach((item) => {
      if (item.kind === 'bag' && item.stock <= 0) return;
      const diff = minutesUntil(item.start);
      if (diff < 0 || diff > lead) return;
      const key = `lb-reminder:${today}:${item.kind}:${item.id}`;
      if (alreadySent(key)) return;
      markSent(key);
      notify(item);
    });
  }

  function startTimer() {
    stopTimer();
    if (!enabled) return;
    check();
    timer = setInterval(check, CHECK_EVERY_MS);
  }
  function stopTimer() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  async function toggle() {
    btn.disabled = true;
    try {
      // minta izin notifikasi hanya saat mengaktifkan (harus dari klik pengguna)
      let permission = canNotify ? Notification.permission : 'unsupported';
      if (!enabled && canNotify && permission === 'default') {
        permission = await Notification.requestPermission();
      }

      const response = await fetch(box.dataset.url, {
        method: 'POST',
        headers: { 'X-CSRFToken': page.dataset.csrf, 'Accept': 'application/json' },
        credentials: 'same-origin',
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || 'Gagal memperbarui pengingat.');

      enabled = data.enabled;
      lead = data.lead_minutes || lead;
      render();

      if (enabled) {
        startTimer();
        if (permission === 'granted') {
          showToast(`Pengingat aktif. Kami ingatkan ${leadLabel()} sebelum jam pickup.`);
        } else {
          showToast('Pengingat aktif, tapi notifikasi browser belum diizinkan. Pengingat akan tampil di halaman ini.');
        }
      } else {
        stopTimer();
        showToast('Pengingat dinonaktifkan.');
      }
    } catch (error) {
      showToast(error.message || 'Gagal memperbarui pengingat, coba lagi.');
    } finally {
      btn.disabled = false;
    }
  }

  btn.addEventListener('click', toggle);
  render();
  startTimer();
})();