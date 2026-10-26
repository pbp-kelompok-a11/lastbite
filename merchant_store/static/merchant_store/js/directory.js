// Direktori toko + peta + filter radius
(() => {
  const root = document.getElementById('store-directory');
  if (!root) return;

  const cfg = {
    searchUrl: root.dataset.searchUrl,
    geocodeUrl: root.dataset.geocodeUrl,
    defaultLat: parseFloat(root.dataset.defaultLat),
    defaultLng: parseFloat(root.dataset.defaultLng),
  };
  const els = {
    q: document.getElementById('ms-q'),
    searchForm: document.getElementById('ms-search-form'),
    locationForm: document.getElementById('ms-location-form'),
    location: document.getElementById('ms-location'),
    useLocation: document.getElementById('ms-use-location'),
    clearLocation: document.getElementById('ms-clear-location'),
    status: document.getElementById('ms-status'),
    results: document.getElementById('ms-results'),
  };
  const state = { center: null, radius: '', q: '' };
  const hasMap = typeof L !== 'undefined';

  //Peta
  let map = null;
  let markersLayer = null;
  let centerMarker = null;
  let radiusCircle = null;
  const markerById = new Map();

  if (hasMap) {
    map = L.map('ms-map').setView([cfg.defaultLat, cfg.defaultLng], 13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      referrerPolicy: 'strict-origin-when-cross-origin',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);
  } else {
    document.getElementById('ms-map').textContent = 'Peta tidak dapat dimuat. Daftar toko tetap tersedia di samping.';
  }

  //Helper DOM
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function setStatus(text, isError = false) {
    els.status.textContent = text;
    els.status.classList.toggle('ms-status--error', isError);
  }

  function ratingText(store) {
    if (store.rating) return `⭐ ${String(store.rating).replace('.', ',')} (${store.rating_count})`;
    return 'Belum ada rating';
  }

  function distanceText(store) {
    if (store.distance_km === null || store.distance_km === undefined) return null;
    return `📍 ${String(store.distance_km).replace('.', ',')} km`;
  }

  function buildPopup(store) {
    const box = el('div');
    const link = el('a', '', store.name);
    link.href = store.detail_url;
    link.style.fontWeight = '700';
    box.appendChild(link);
    box.appendChild(el('div', '', store.address));
    box.appendChild(el('div', '', `🕐 ${store.hours}`));
    return box;
  }

  function buildCard(store) {
    const card = el('li', 'ms-card');
    const main = el('div', 'ms-card__main');

    const title = el('h3');
    const link = el('a', '', store.name);
    link.href = store.detail_url;
    title.appendChild(link);
    main.appendChild(title);
    main.appendChild(el('span', `ms-badge ${store.is_open ? 'ms-badge--open' : 'ms-badge--closed'}`, store.is_open ? 'Buka' : 'Tutup'));
    main.appendChild(el('p', 'ms-card__address', store.address));

    const meta = el('p', 'ms-card__meta');
    meta.appendChild(el('span', '', `🕐 ${store.hours}`));
    meta.appendChild(el('span', '', ratingText(store)));
    const distance = distanceText(store);
    if (distance) meta.appendChild(el('span', '', distance));
    if (store.latitude === null) meta.appendChild(el('span', '', 'Lokasi belum ada di peta'));
    main.appendChild(meta);
    card.appendChild(main);

    const actions = el('div', 'ms-card__actions');
    if (hasMap && store.latitude !== null) {
      const focusBtn = el('button', 'btn btn--ghost btn--sm', 'Lihat di peta');
      focusBtn.type = 'button';
      focusBtn.addEventListener('click', () => {
        const marker = markerById.get(store.id);
        if (!marker) return;
        map.flyTo(marker.getLatLng(), 17);
        marker.openPopup();
        document.getElementById('ms-map').scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
      actions.appendChild(focusBtn);
    }
    if (store.wishlist_url) {
      const wishBtn = el('button', 'btn btn--outline btn--sm js-wishlist-toggle');
      wishBtn.type = 'button';
      wishBtn.dataset.url = store.wishlist_url;
      if (window.setWishlistButtonState) window.setWishlistButtonState(wishBtn, store.wishlisted);
      actions.appendChild(wishBtn);
    }
    card.appendChild(actions);
    return card;
  }

  //Render hasil
  function render(data) {
    els.results.replaceChildren();
    if (hasMap) markersLayer.clearLayers();
    markerById.clear();

    data.stores.forEach((store) => {
      els.results.appendChild(buildCard(store));
      if (hasMap && store.latitude !== null && store.longitude !== null) {
        const marker = L.marker([store.latitude, store.longitude]).bindPopup(buildPopup(store));
        marker.addTo(markersLayer);
        markerById.set(store.id, marker);
      }
    });

    const where = state.center && state.radius ? ` dalam radius ${state.radius} km` : '';
    const hint = state.radius && !state.center
      ? ' Tentukan lokasimu dulu (tombol "Gunakan lokasi saya" atau ketik lokasi) agar filter radius berlaku.'
      : '';
    setStatus((data.count === 0 ? `Tidak ada toko ditemukan${where}.` : `${data.count} toko ditemukan${where}.`) + hint);
    fitMap();
  }

  function fitMap() {
    if (!hasMap) return;
    const points = [...markerById.values()].map((m) => m.getLatLng());
    if (state.center) points.push(L.latLng(state.center.lat, state.center.lng));
    if (radiusCircle) {
      map.fitBounds(radiusCircle.getBounds(), { padding: [30, 30] });
    } else if (points.length > 1) {
      map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 16 });
    } else if (points.length === 1) {
      map.setView(points[0], 15);
    }
  }

  function updateCenterOverlay() {
    if (!hasMap) return;
    if (centerMarker) { map.removeLayer(centerMarker); centerMarker = null; }
    if (radiusCircle) { map.removeLayer(radiusCircle); radiusCircle = null; }
    if (!state.center) return;
    centerMarker = L.circleMarker([state.center.lat, state.center.lng], {
      radius: 8, color: '#1F4D39', fillColor: '#F29F58', fillOpacity: 1, weight: 3,
    }).addTo(map).bindTooltip('Lokasimu');
    if (state.radius) {
      radiusCircle = L.circle([state.center.lat, state.center.lng], {
        radius: parseFloat(state.radius) * 1000,
        color: '#2F694F', fillColor: '#2F694F', fillOpacity: 0.08, weight: 2,
      }).addTo(map);
    }
  }

  // ambil data (asinkron)
  let controller = null;
  async function loadStores() {
    if (controller) controller.abort();
    controller = new AbortController();

    const params = new URLSearchParams();
    if (state.q) params.set('q', state.q);
    if (state.center) {
      params.set('lat', state.center.lat);
      params.set('lng', state.center.lng);
      if (state.radius) params.set('radius', state.radius);
    }
    setStatus('Memuat toko…');
    updateCenterOverlay();

    try {
      const response = await fetch(`${cfg.searchUrl}?${params}`, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Gagal memuat toko.');
      render(data);
    } catch (error) {
      if (error.name === 'AbortError') return;
      setStatus(error.message || 'Terjadi kesalahan saat memuat toko.', true);
    }
  }

  function setCenter(center) {
    state.center = center;
    els.clearLocation.hidden = false;
    loadStores();
  }

  // Event
  let debounceTimer = null;
  els.q.addEventListener('input', () => {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => {
      state.q = els.q.value.trim();
      loadStores();
    }, 350);
  });
  els.searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    window.clearTimeout(debounceTimer);
    state.q = els.q.value.trim();
    loadStores();
  });

  document.querySelectorAll('input[name="radius"]').forEach((radio) => {
    radio.addEventListener('change', () => {
      state.radius = radio.value;
      loadStores();
    });
  });

  els.useLocation.addEventListener('click', () => {
    if (!navigator.geolocation) {
      setStatus('Browser kamu tidak mendukung geolokasi. Ketik nama lokasi di kolom "Lokasimu".', true);
      return;
    }
    setStatus('Mencari lokasimu…');
    navigator.geolocation.getCurrentPosition(
      (position) => setCenter({ lat: position.coords.latitude, lng: position.coords.longitude }),
      () => setStatus('Tidak bisa mengambil lokasi. Izinkan akses lokasi di browser atau ketik nama lokasi.', true),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  });

  els.locationForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = els.location.value.trim();
    if (query.length < 3) {
      setStatus('Ketik minimal 3 karakter untuk mencari lokasi.', true);
      return;
    }
    setStatus('Mencari lokasi…');
    try {
      const response = await fetch(`${cfg.geocodeUrl}?q=${encodeURIComponent(query)}`, {
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Lokasi tidak ditemukan.');
      setCenter({ lat: data.lat, lng: data.lng });
    } catch (error) {
      setStatus(error.message || 'Terjadi kesalahan saat mencari lokasi.', true);
    }
  });

  els.clearLocation.addEventListener('click', () => {
    state.center = null;
    els.location.value = '';
    els.clearLocation.hidden = true;
    loadStores();
  });

  loadStores();
})();
