const searchForm = document.querySelector('.community-search');

if (searchForm) {
  // Elemen pencarian dan filter pada halaman Community.
  const searchInput = searchForm.querySelector('[name="q"]');
  const categoryInput = searchForm.querySelector('[name="post_type"]');
  const sortSelect = document.getElementById('community-sort');
  const ratingSelect = document.getElementById('community-rating');
  const ratingFilter = document.querySelector('.community-rating-filter');
  const searchLabel = searchForm.querySelector('label[for="community-query"]');
  const likedSelect = document.getElementById('community-liked');
  const mineSelect = document.getElementById('community-mine');
  const mineFilter = document.querySelector('.community-mine-filter');
  const likedFilter = document.querySelector('.community-food-hack-filter');
  const tabs = document.querySelector('.community-tabs');
  const searchStatus = document.getElementById('community-search-status');
  const feedHeading = document.getElementById('food-hacks-title');

  // Simpan hasil saat ini dan status request yang sedang berjalan.
  let feedResults = document.getElementById('community-results');
  let searchTimer;
  let statusTimer;
  let searchController;
  let requestSequence = 0;

  // Batalkan pencarian lama sebelum memulai pencarian baru.
  function cancelPendingSearch() {
    window.clearTimeout(searchTimer);
    window.clearTimeout(statusTimer);
    searchController?.abort();

    // Abaikan respons lama jika user sudah mengganti pencarian.
    requestSequence += 1;
    feedResults.removeAttribute('aria-busy');
  }

  // Susun parameter URL dari kategori, filter, dan nomor halaman.
  function buildFeedUrl(postType = categoryInput.value, page = 1) {
    const url = new URL(searchForm.action);
    url.searchParams.set('post_type', postType);
    if (mineSelect?.value === '1' && postType === 'all') {
      url.searchParams.set('mine', '1');
    }
    const query = searchInput.value.trim();
    if (query) {
      url.searchParams.set('q', query);
    }
    if (sortSelect.value !== 'newest' && postType === categoryInput.value) {
      url.searchParams.set('sort', sortSelect.value);
    }
    if (likedSelect.value === '1' && postType === 'food_hack') {
      url.searchParams.set('liked', '1');
    }
    if (postType === 'review' && ratingSelect.value !== 'all') {
      url.searchParams.set('rating', ratingSelect.value);
    }
    if (page > 1) {
      url.searchParams.set('page', page);
    }
    return url;
  }

  // Sesuaikan kontrol dan tautan dengan hasil yang dikembalikan server.
  function updateFeedControls(url, postType) {
    // Ikuti nilai server karena filter atau nomor halaman bisa disesuaikan.
    const actualPage = Number(feedResults.dataset.page);
    if (actualPage > 1) {
      url.searchParams.set('page', actualPage);
    }
    else {
      url.searchParams.delete('page');
    }
    feedHeading.textContent = feedResults.dataset.heading;
    if (mineSelect) {
      mineSelect.value = feedResults.dataset.mine;
    }
    if (mineFilter) {
      mineFilter.hidden = postType !== 'all';
    }
    if (feedResults.dataset.mine !== '1') {
      url.searchParams.delete('mine');
    }
    sortSelect.replaceChildren(feedResults.querySelector('#community-sort-options').content.cloneNode(true));
    sortSelect.value = feedResults.dataset.sort;
    if (sortSelect.value === 'newest') {
      url.searchParams.delete('sort');
    }
    else {
      url.searchParams.set('sort', sortSelect.value);
    }
    likedSelect.value = feedResults.dataset.liked;
    likedFilter.hidden = postType !== 'food_hack';
    if (likedSelect.value !== '1') {
      url.searchParams.delete('liked');
    }
    ratingSelect.value = feedResults.dataset.rating;
    ratingFilter.hidden = postType !== 'review';
    if (ratingSelect.value === 'all') {
      url.searchParams.delete('rating');
    }
    else {
      url.searchParams.set('rating', ratingSelect.value);
    }
    searchLabel.textContent = feedResults.dataset.searchLabel;
    searchInput.placeholder = feedResults.dataset.searchPlaceholder;
    tabs.querySelectorAll('a').forEach((tab) => {
      const type = new URL(tab.href).searchParams.get('post_type');
      const active = type === postType;
      tab.classList.toggle('community-tab--active', active);
      if (active) {
        tab.setAttribute('aria-current', 'page');
      }
      else {
        tab.removeAttribute('aria-current');
      }
      tab.href = buildFeedUrl(type).href;
    });
  }

  // Ambil HTML hasil pencarian tanpa memuat ulang seluruh halaman.
  async function loadFeed(page = 1, scrollToResults = false) {
    cancelPendingSearch();
    const requestId = requestSequence;
    searchController = new AbortController();
    const url = buildFeedUrl(categoryInput.value, page);
    const postType = categoryInput.value;
    feedResults.setAttribute('aria-busy', 'true');
    searchStatus.textContent = 'Mencari postingan…';
    searchStatus.hidden = false;

    try {
      const response = await fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        signal: searchController.signal,
        credentials: 'same-origin',
        mode: 'same-origin',
      });

      // Filter pribadi memerlukan login.
      if (response.status === 401) {
        const data = await response.json();
        if (requestId !== requestSequence) {
          return;
        }
        if (data.login_url) {
          window.location.assign(data.login_url);
        }
        return;
      }
      if (!response.ok) {
        throw new Error('Search failed');
      }

      // Ganti hasil hanya jika respons masih milik pencarian terbaru.

      const html = await response.text();
      if (requestId !== requestSequence) {
        return;
      }
      const documentFragment = new DOMParser().parseFromString(html, 'text/html');
      const updated = documentFragment.getElementById('community-results');
      if (!updated) {
        throw new Error('Missing search results');
      }
      feedResults.replaceWith(updated);
      feedResults = updated;
      updateFeedControls(url, postType);
      window.history.replaceState(null, '', url);

      // Saat pindah halaman, arahkan fokus ke hasil yang baru.
      if (scrollToResults) {
        feedResults.querySelector('.community-page--current')?.focus({ preventScroll: true });
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        feedResults.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
      }
      searchStatus.textContent = 'Hasil pencarian diperbarui.';
      statusTimer = window.setTimeout(() => {
        searchStatus.hidden = true;
      }, 1000);
    } catch (error) {
      if (error.name === 'AbortError' || requestId !== requestSequence) {
        return;
      }
      searchStatus.textContent = 'Pencarian gagal. Hasil sebelumnya tetap ditampilkan. Tekan Cari untuk mencoba lagi.';
    } finally {
      if (requestId === requestSequence) {
        feedResults.removeAttribute('aria-busy');
      }
    }
  }

  function scheduleSearch() {
    cancelPendingSearch();
    searchStatus.hidden = true;

    // Tunggu sebentar agar tidak mengirim request untuk setiap ketikan.
    searchTimer = window.setTimeout(loadFeed, 350);
  }

  // Pencarian mengikuti ketikan; filter lain dimuat saat pilihannya berubah.
  searchInput.addEventListener('input', (event) => {
    if (!event.isComposing) {
      scheduleSearch();
    }
  });
  searchInput.addEventListener('compositionstart', cancelPendingSearch);
  searchInput.addEventListener('compositionend', scheduleSearch);
  sortSelect.addEventListener('change', () => loadFeed());
  ratingSelect.addEventListener('change', () => loadFeed());
  likedSelect.addEventListener('change', () => loadFeed());
  mineSelect?.addEventListener('change', () => loadFeed());

  // Perbarui feed jika like memengaruhi filter atau urutan saat ini.
  document.addEventListener('community:like-changed', () => {
    if (likedSelect.value === '1' || sortSelect.value === 'likes') {
      loadFeed(Number(feedResults.dataset.page));
    }
  });
  searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    loadFeed();
  });

  // Ctrl, Shift, dan klik tengah tetap memakai perilaku tautan bawaan browser.
  function isPlainClick(event) {
    return event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;
  }

  // Pindah kategori mengembalikan filter khusus tab ke nilai awal.
  tabs.addEventListener('click', (event) => {
    const tab = event.target.closest('a');
    if (!tab || !isPlainClick(event)) {
      return;
    }
    event.preventDefault();
    const nextCategory = new URL(tab.href).searchParams.get('post_type');
    if (nextCategory === categoryInput.value) {
      return;
    }
    categoryInput.value = nextCategory;
    if (mineSelect) {
      mineSelect.value = '0';
    }
    sortSelect.value = 'newest';
    likedSelect.value = '0';
    ratingSelect.value = 'all';
    loadFeed();
  });

  // Tangani pagination dan hapus kata kunci dari area hasil.
  document.getElementById('community-results').parentElement.addEventListener('click', (event) => {
    const pageLink = event.target.closest('[data-page-link]');
    if (pageLink && isPlainClick(event)) {
      event.preventDefault();
      loadFeed(Number(pageLink.dataset.pageLink), true);
      return;
    }
    if (!event.target.closest('[data-clear-search]') || !isPlainClick(event)) {
      return;
    }
    event.preventDefault();
    searchInput.value = '';
    loadFeed();
    searchInput.focus();
  });
}
