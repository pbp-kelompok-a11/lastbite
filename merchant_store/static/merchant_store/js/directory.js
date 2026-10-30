// Halaman Merchants: daftar toko + peta + filter radius (data dimuat via AJAX)
(() => {
  const root = document.getElementById("store-directory");
  if (!root) return;

  const cfg = {
    searchUrl: root.dataset.searchUrl,
    geocodeUrl: root.dataset.geocodeUrl,
    defaultLat: parseFloat(root.dataset.defaultLat),
    defaultLng: parseFloat(root.dataset.defaultLng),
    thumbs: (root.dataset.thumbs || "").split("|").filter(Boolean),
  };
  const els = {
    q: document.getElementById("md-q"),
    searchForm: document.getElementById("md-search-form"),
    chips: document.querySelectorAll(".md-chip"),
    locationForm: document.getElementById("md-location-form"),
    location: document.getElementById("md-location"),
    useLocation: document.getElementById("md-use-location"),
    clearLocation: document.getElementById("md-clear-location"),
    status: document.getElementById("md-status"),
    list: document.getElementById("md-list"),
    countNum: document.getElementById("md-count-num"),
    countArea: document.getElementById("md-count-area"),
  };
  const state = { center: null, radius: "", q: "" };
  const hasMap = typeof L !== "undefined";

  const PIN_HTML =
    '<span class="md-pin"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M6 8h12l-1 12H7L6 8Z"/><path d="M9 8a3 3 0 0 1 6 0"/></svg></span>';
  const ARROW_SVG =
    '<svg class="md-item__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M5 12h14M13 6l6 6-6 6"/></svg>';
  const PIN_BTN_SVG =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z"/><circle cx="12" cy="10" r="2.5"/></svg>';

  // ---------- Peta ----------
  let map = null;
  let markersLayer = null;
  let meMarker = null;
  let radiusCircle = null;
  const markerById = new Map();

  if (hasMap) {
    map = L.map("md-map").setView([cfg.defaultLat, cfg.defaultLng], 14);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      referrerPolicy: "strict-origin-when-cross-origin",
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);
    // jaga ukuran peta tetap sinkron dengan kotaknya, lalu pusatkan ulang
    if (typeof ResizeObserver !== "undefined") {
      let resizeTimer = null;
      new ResizeObserver(() => {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(() => {
          map.invalidateSize();
          fitMap();
        }, 120);
      }).observe(document.getElementById("md-map"));
    }
  } else {
    document.getElementById("md-map").textContent =
      "Peta tidak dapat dimuat. Daftar toko tetap tersedia di samping.";
  }

  // ---------- Helper ----------
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function comma(value) {
    return String(value).replace(".", ",");
  }

  function setStatus(text, isError = false) {
    els.status.textContent = text;
    els.status.hidden = !text;
    els.status.classList.toggle("md-status--error", isError);
  }

  function setActiveChip(radius) {
    els.chips.forEach((chip) => {
      chip.setAttribute(
        "aria-pressed",
        chip.dataset.radius === radius ? "true" : "false",
      );
    });
  }

  function ratingLine(store) {
    const parts = [];
    parts.push(store.rating ? `★ ${comma(store.rating)}` : "Belum ada rating");
    if (store.distance_km !== null && store.distance_km !== undefined) {
      parts.push(`${comma(store.distance_km)} km`);
    }
    return parts.join(" · ");
  }

  function metaLine(store) {
    const bags =
      store.bag_count > 0
        ? `${store.bag_count} Surprise Bag tersedia`
        : "Belum ada Surprise Bag tersedia";
    return `${bags} · ${store.address}`;
  }

  function setPinActive(id, active) {
    const marker = markerById.get(id);
    if (!marker || !marker.getElement()) return;
    const pin = marker.getElement().querySelector(".md-pin");
    if (pin) pin.classList.toggle("is-active", active);
  }

  function buildPopup(store) {
    const box = el("div");
    const link = el("a", "md-popup__name", store.name);
    link.href = store.detail_url;
    box.appendChild(link);
    box.appendChild(el("div", "md-popup__addr", store.address));
    box.appendChild(
      el("div", "md-popup__hours", `🕐 ${store.hours} · ${store.is_open ? "Buka" : "Tutup"}`),
    );
    return box;
  }

  function buildItem(store) {
    const item = el("li", "md-item");
    const link = el("a", "md-item__link");
    link.href = store.detail_url;

    const thumb = el("div", "md-item__thumb");
    if (store.photo_url) {
      const img = el("img", "md-item__photo");
      img.src = store.photo_url;
      img.alt = store.name;
      thumb.appendChild(img);
    } else if (cfg.thumbs.length) {
      const img = el("img");
      img.src = cfg.thumbs[store.id % cfg.thumbs.length];
      img.alt = "";
      thumb.appendChild(img);
    }
    
    link.appendChild(thumb);

    const body = el("div", "md-item__body");
    body.appendChild(el("div", "md-item__name", store.name));

    const rating = el("div", "md-item__rating");
    rating.appendChild(el("span", "", ratingLine(store)));
    rating.appendChild(
      el(
        "span",
        `md-badge ${store.is_open ? "md-badge--open" : "md-badge--closed"}`,
        `${store.is_open ? "Buka" : "Tutup"} · ${store.hours}`,
      ),
    );
    body.appendChild(rating);
    body.appendChild(el("div", "md-item__meta", metaLine(store)));
    link.appendChild(body);

    link.insertAdjacentHTML("beforeend", ARROW_SVG);
    item.appendChild(link);

    // tombol aksi: lihat di peta + wishlist (khusus customer)
    const actions = el("div", "md-item__actions");
    if (hasMap) {
      const focusBtn = el("button", "md-icon-btn");
      focusBtn.type = "button";
      focusBtn.title = "Lihat di peta";
      focusBtn.setAttribute("aria-label", `Lihat ${store.name} di peta`);
      focusBtn.innerHTML = PIN_BTN_SVG;
      focusBtn.addEventListener("click", () => {
        const marker = markerById.get(store.id);
        if (!marker) {
          // toko belum punya koordinat: buka halaman detail yang menampilkan petanya
          window.location.href = store.detail_url;
          return;
        }
        map.flyTo(marker.getLatLng(), 17);
        marker.openPopup();
        document
          .getElementById("md-map")
          .scrollIntoView({ behavior: "smooth", block: "center" });
      });
      actions.appendChild(focusBtn);
    }
    if (store.wishlist_url) {
      const wishBtn = el("button", "md-icon-btn md-icon-btn--wish js-wishlist-toggle");
      wishBtn.type = "button";
      wishBtn.dataset.url = store.wishlist_url;
      wishBtn.setAttribute("data-icon-only", "");
      if (window.setWishlistButtonState) {
        window.setWishlistButtonState(wishBtn, store.wishlisted);
      }
      actions.appendChild(wishBtn);
    }
    if (actions.children.length) item.appendChild(actions);

    // sorot pin di peta saat daftar di-hover / difokus
    link.addEventListener("mouseenter", () => setPinActive(store.id, true));
    link.addEventListener("mouseleave", () => setPinActive(store.id, false));
    link.addEventListener("focus", () => setPinActive(store.id, true));
    link.addEventListener("blur", () => setPinActive(store.id, false));
    return item;
  }

  // ---------- Render ----------
  function render(data) {
    els.list.replaceChildren();
    if (hasMap) markersLayer.clearLayers();
    markerById.clear();

    if (data.stores.length === 0) {
      els.list.appendChild(
        el("li", "md-empty", "Tidak ada toko yang cocok dengan pencarianmu."),
      );
    }

    data.stores.forEach((store) => {
      els.list.appendChild(buildItem(store));
      if (hasMap && store.latitude !== null && store.longitude !== null) {
        const icon = L.divIcon({
          className: "md-pin-wrap",
          html: PIN_HTML,
          iconSize: [36, 36],
          iconAnchor: [18, 43],
          popupAnchor: [0, -40],
        });
        const marker = L.marker([store.latitude, store.longitude], {
          icon,
          title: store.name,
        }).bindPopup(buildPopup(store));
        marker.addTo(markersLayer);
        markerById.set(store.id, marker);
      }
    });

    els.countNum.textContent = `${data.count} merchant`;
    els.countArea.textContent = state.center
      ? state.radius
        ? `dalam radius ${state.radius} km`
        : "di sekitar lokasimu"
      : "di semua area";
    const where = state.center && state.radius ? ` dalam radius ${state.radius} km` : "";
    setStatus(data.count > 0 ? `${data.count} toko ditemukan${where}.` : "");
    fitMap();
  }

  function fitMap() {
    if (!hasMap) return;
        map.invalidateSize();
    if (radiusCircle) {
      map.fitBounds(radiusCircle.getBounds(), { padding: [30, 30] });
      return;
    }
    const points = [...markerById.values()].map((m) => m.getLatLng());
    if (state.center) points.push(L.latLng(state.center.lat, state.center.lng));
    if (points.length > 1) {
      map.fitBounds(L.latLngBounds(points), { padding: [60, 60], maxZoom: 16 });
    } else if (points.length === 1) {
      map.setView(points[0], 15);
    }
  }

  function updateCenterOverlay() {
    if (!hasMap) return;
    if (meMarker) {
      map.removeLayer(meMarker);
      meMarker = null;
    }
    if (radiusCircle) {
      map.removeLayer(radiusCircle);
      radiusCircle = null;
    }
    if (!state.center) return;

    meMarker = L.marker([state.center.lat, state.center.lng], {
      icon: L.divIcon({
        className: "md-pin-wrap",
        html: '<span class="md-me"></span>',
        iconSize: [16, 16],
      }),
      interactive: false,
    }).addTo(map);

    if (state.radius) {
      radiusCircle = L.circle([state.center.lat, state.center.lng], {
        radius: parseFloat(state.radius) * 1000,
        color: "#1f7d58",
        fillColor: "#1f7d58",
        fillOpacity: 0.08,
        weight: 2,
      }).addTo(map);
    }
  }

  // ---------- Ambil data (AJAX) ----------
  let controller = null;
  async function loadStores() {
    if (controller) controller.abort();
    controller = new AbortController();

    const params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.center) {
      params.set("lat", state.center.lat);
      params.set("lng", state.center.lng);
      if (state.radius) params.set("radius", state.radius);
    }
    updateCenterOverlay();

    try {
      const response = await fetch(`${cfg.searchUrl}?${params}`, {
        signal: controller.signal,
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Gagal memuat toko.");
      render(data);
    } catch (error) {
      if (error.name === "AbortError") return;
      setStatus(error.message || "Terjadi kesalahan saat memuat toko.", true);
    }
  }

  // Minta lokasi pengguna; resolve null jika gagal
  function requestLocation() {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null);
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) =>
          resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => resolve(null),
        { enableHighAccuracy: true, timeout: 10000 },
      );
    });
  }

  function setCenter(center) {
    state.center = center;
    els.clearLocation.hidden = false;
    loadStores();
  }

  // ---------- Event ----------
  let debounceTimer = null;
  els.q.addEventListener("input", () => {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => {
      state.q = els.q.value.trim();
      loadStores();
    }, 350);
  });
  els.searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    window.clearTimeout(debounceTimer);
    state.q = els.q.value.trim();
    loadStores();
  });

  els.chips.forEach((chip) => {
    chip.addEventListener("click", async () => {
      const value = chip.dataset.radius;

      // klik chip yang sedang aktif = matikan filter radius
      if (state.radius === value) {
        state.radius = "";
        setActiveChip("");
        loadStores();
        return;
      }

      // filter radius butuh lokasi pengguna
      if (!state.center) {
        setStatus("Mencari lokasimu…");
        const center = await requestLocation();
        if (!center) {
          state.radius = "";
          setActiveChip("");
          setStatus(
            "Tidak bisa mengambil lokasi. Izinkan akses lokasi di browser agar filter radius bisa dipakai.",
            true,
          );
          return;
        }
        state.center = center;
      }

      state.radius = value;
      setActiveChip(value);
      loadStores();
    });
  });

  els.useLocation.addEventListener("click", async () => {
    setStatus("Mencari lokasimu…");
    const center = await requestLocation();
    if (!center) {
      setStatus(
        "Tidak bisa mengambil lokasi. Izinkan akses lokasi di browser atau ketik nama lokasi.",
        true,
      );
      return;
    }
    setCenter(center);
  });

  els.locationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = els.location.value.trim();
    if (query.length < 3) {
      setStatus("Ketik minimal 3 karakter untuk mencari lokasi.", true);
      return;
    }
    setStatus("Mencari lokasi…");
    try {
      const response = await fetch(
        `${cfg.geocodeUrl}?q=${encodeURIComponent(query)}`,
        {
          headers: { Accept: "application/json" },
          credentials: "same-origin",
        },
      );
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.error || "Lokasi tidak ditemukan.");
      setCenter({ lat: data.lat, lng: data.lng });
    } catch (error) {
      setStatus(
        error.message || "Terjadi kesalahan saat mencari lokasi.",
        true,
      );
    }
  });

  els.clearLocation.addEventListener("click", () => {
    state.center = null;
    state.radius = "";
    setActiveChip("");
    els.location.value = "";
    els.clearLocation.hidden = true;
    loadStores();
  });
  loadStores();
})();
