// Halaman detail toko: peta OpenStreetMap (Leaflet) selalu tampil,
// pin + label nama toko muncul setelah lokasi toko ditemukan
(() => {
  const el = document.getElementById('ms-detail-map');
  if (!el || typeof L === 'undefined') return;

  const status = document.getElementById('ms-map-status');
  const openLink = document.getElementById('ms-open-osm-link');

  // ---------- Pengaman struktur HTML ----------
  // Pastikan hanya ada satu peta/status/link, semuanya berada DI DALAM kotak peta
  // (.ms-profile-map-panel), dan ilustrasi abu-abu dihapus karena diganti peta asli.
  const panel = document.querySelector('.ms-profile-map-panel');
  [el, status, openLink].forEach((node) => {
    if (!node) return;
    document.querySelectorAll('#' + node.id).forEach((dup) => {
      if (dup !== node) dup.remove();
    });
    if (panel && !panel.contains(node)) panel.appendChild(node);
  });

  // Bar rating bintang harus berada di dalam halaman, tepat di bawah kartu utama
  const page = document.querySelector('.ms-store-detail-page');
  const layout = page ? page.querySelector('.ms-profile-layout') : null;
  const ratingBar = document.getElementById('ms-store-rating');
  if (page && layout && ratingBar && ratingBar.previousElementSibling !== layout) {
    layout.after(ratingBar);
  }

  document
    .querySelectorAll('.ms-map-illustration, .ms-map-callout, .ms-map-pin, .ms-illustration-road')
    .forEach((node) => node.remove());
  el.classList.add('is-ready');

  // Dipakai bila lokasi toko belum diketahui: tampilan Indonesia
  const FALLBACK_CENTER = [-2.5489, 118.0149];
  const FALLBACK_ZOOM = 5;

  const PIN_HTML =
    '<span class="ms-detail-pin"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M6 8h12l-1 12H7L6 8Z"/><path d="M9 8a3 3 0 0 1 6 0"/></svg></span>';

  function showStatus(message) {
    if (status) {
      status.textContent = message;
      status.hidden = false;
    }
  }

  function hideStatus() {
    if (status) {
      status.textContent = '';
      status.hidden = true;
    }
  }

  function validCoordinates(lat, lng) {
    return Number.isFinite(lat) &&
      Number.isFinite(lng) &&
      lat >= -90 && lat <= 90 &&
      lng >= -180 && lng <= 180;
  }

  // Isi label: nama toko + "di area ..." (dibuat lewat DOM agar aman dari XSS)
  function buildCallout() {
    const box = document.createElement('div');
    const name = document.createElement('strong');
    name.textContent = (el.dataset.name || 'Lokasi toko').toUpperCase();
    box.appendChild(name);

    const words = (el.dataset.address || '').trim().split(/\s+/).filter(Boolean);
    if (words.length) {
      const area = document.createElement('small');
      area.textContent = `di area ${words.slice(0, 3).join(' ')}${words.length > 3 ? ' …' : ''}`;
      box.appendChild(area);
    }
    return box;
  }

  // ---------- Peta dibuat langsung, tanpa menunggu lokasi toko ----------
  const map = L.map(el, {
    zoomControl: true,
    scrollWheelZoom: true,
  }).setView(FALLBACK_CENTER, FALLBACK_ZOOM);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">' +
      'OpenStreetMap</a> contributors',
    referrerPolicy: 'strict-origin-when-cross-origin',
  }).addTo(map);

  requestAnimationFrame(() => map.invalidateSize());

  // ---------- Pin toko ----------
  function placeStore(lat, lng, zoom = 16) {
    if (!validCoordinates(lat, lng)) {
      showStatus('Koordinat lokasi toko tidak valid.');
      return;
    }

    const icon = L.divIcon({
      className: 'ms-detail-pin-wrap',
      html: PIN_HTML,
      iconSize: [38, 38],
      iconAnchor: [19, 44],
    });

    L.marker([lat, lng], { icon, title: el.dataset.name || 'Lokasi toko' })
      .addTo(map)
      .bindTooltip(buildCallout(), {
        permanent: true,
        direction: 'top',
        offset: [0, -46],
        className: 'ms-detail-callout',
      });

    map.setView([lat, lng], zoom);

    if (openLink) {
      openLink.href =
        `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}` +
        `#map=16/${lat}/${lng}`;
    }
    hideStatus();
  }

  // ---------- Cari lokasi toko dari alamat ----------
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // Bersihkan alamat: buang kode pos, "Indonesia", dan bagian yang berulang
  function cleanParts(address) {
    const seen = new Set();
    const parts = [];
    address.split(',').forEach((raw) => {
      const part = raw.replace(/\b\d{5}\b/g, '').replace(/\s+/g, ' ').trim();
      if (!part || /^indonesia$/i.test(part)) return;
      const key = part.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      parts.push(part);
    });
    return parts;
  }

  // Alamat lengkap dulu, lalu versi yang makin ringkas (nama + kecamatan + kabupaten/kota)
  function candidateQueries(address) {
    const parts = cleanParts(address);
    const list = [];
    const add = (query) => {
      const text = (query || '').trim();
      if (text.length >= 3 && !list.includes(text)) list.push(text);
    };

    add(address);

    const kec = parts.find((p) => /^kec(amatan)?\.?\s/i.test(p));
    const kab = parts.find((p) => /^(kabupaten|kab\.|kota)\s/i.test(p));
    const kecName = kec ? kec.replace(/^kec(amatan)?\.?\s+/i, '') : '';

    if (kecName && kab) {
      add(`${parts[0]}, ${kecName}, ${kab}`);
      add(`${kecName}, ${kab}`);
    } else {
      add(parts.slice(0, 3).join(', '));
    }
    add(parts.slice(-2).join(', '));

    return list.slice(0, 4);
  }

  // null = tidak ditemukan; melempar Error bila layanan bermasalah
  async function geocodeOnce(endpoint, query) {
    const url = new URL(endpoint, window.location.origin);
    url.searchParams.set('q', query.slice(0, 250));

    const response = await fetch(url, {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    });
    const data = await response.json().catch(() => ({}));

    if (response.status === 404) return null;
    if (!response.ok) {
      throw new Error(data.error || 'Layanan peta tidak dapat dihubungi.');
    }
    return data;
  }

  async function loadStoreLocation() {
    const lat = Number(el.dataset.lat);
    const lng = Number(el.dataset.lng);

    if (el.dataset.lat && el.dataset.lng && validCoordinates(lat, lng)) {
      placeStore(lat, lng);
      return;
    }

    const address = (el.dataset.address || '').trim();
    const endpoint = el.dataset.geocodeUrl;

    if (!address || !endpoint) {
      showStatus('Alamat toko belum tersedia, jadi pin lokasi belum bisa ditampilkan.');
      return;
    }

    const queries = candidateQueries(address);

    try {
      for (let i = 0; i < queries.length; i += 1) {
        if (i > 0) await sleep(1100); // patuhi batas 1 permintaan/detik Nominatim
        showStatus(i === 0 ? 'Mencari lokasi toko...' : 'Mencari lokasi perkiraan toko...');

        const result = await geocodeOnce(endpoint, queries[i]);
        if (!result) continue;

        const foundLat = Number(result.lat);
        const foundLng = Number(result.lng);
        if (!validCoordinates(foundLat, foundLng)) continue;

        placeStore(foundLat, foundLng, 16);
        return;
      }

      showStatus('Lokasi toko belum ditemukan di peta. Coba perpendek alamat toko.');
    } catch (error) {
      console.error('Gagal memuat lokasi toko:', error);
      showStatus(error.message || 'Lokasi toko tidak dapat dimuat.');
    }
  }

  loadStoreLocation();
})();