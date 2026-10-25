//Peta di halaman detail toko
(() => {
  const el = document.getElementById('ms-detail-map');
  if (!el || typeof L === 'undefined') return;

  const lat = parseFloat(el.dataset.lat);
  const lng = parseFloat(el.dataset.lng);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return;

  const map = L.map(el).setView([lat, lng], 16);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  const popup = document.createElement('strong');
  popup.textContent = el.dataset.name || 'Lokasi toko';
  L.marker([lat, lng]).addTo(map).bindPopup(popup).openPopup();
})();
