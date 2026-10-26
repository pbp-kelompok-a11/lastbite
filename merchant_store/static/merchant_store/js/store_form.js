// Pratinjau lokasi alamat lewat OpenStreetMap Nominatim
(() => {
  const form = document.getElementById('ms-store-form');
  const button = document.getElementById('ms-check-location');
  const statusEl = document.getElementById('ms-geocode-status');
  const mapEl = document.getElementById('ms-form-map');
  const addressInput = document.getElementById('id_address');
  if (!form || !button || !statusEl || !mapEl || !addressInput) return;

  let map = null;
  let marker = null;

  function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.classList.toggle('ms-status--error', isError);
  }

  function showOnMap(lat, lng) {
    if (typeof L === 'undefined') return;
    mapEl.hidden = false;
    if (!map) {
      map = L.map(mapEl);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);
    }
    map.setView([lat, lng], 17);
    if (marker) marker.setLatLng([lat, lng]); else marker = L.marker([lat, lng]).addTo(map);
    map.invalidateSize();
  }

  button.addEventListener('click', async () => {
    const address = addressInput.value.trim();
    if (address.length < 3) {
      setStatus('Isi alamat terlebih dahulu.', true);
      return;
    }
    button.disabled = true;
    setStatus('Mencari lokasi…');
    try {
      const response = await fetch(`${form.dataset.geocodeUrl}?q=${encodeURIComponent(address)}`, {
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Lokasi tidak ditemukan.');
      setStatus(`Ditemukan: ${data.display_name}`);
      showOnMap(data.lat, data.lng);
    } catch (error) {
      setStatus(error.message || 'Terjadi kesalahan.', true);
    } finally {
      button.disabled = false;
    }
  });
})();
