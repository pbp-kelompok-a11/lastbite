(() => {
  const tabs = document.querySelectorAll('.mw-tab');
  const panels = document.querySelectorAll('.mw-panel');
  if (!tabs.length) return;

  function selectTab(name) {
    tabs.forEach((tab) => {
      const active = tab.dataset.tab === name;
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.tabIndex = active ? 0 : -1;
    });
    panels.forEach((panel) => { panel.hidden = panel.dataset.panel !== name; });
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectTab(tab.dataset.tab));
    tab.addEventListener('keydown', (event) => {
      if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
      const next = tabs[(index + (event.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      next.focus();
      selectTab(next.dataset.tab);
    });
  });

  // jumlah & pesan kosong di tiap tab ikut berubah saat kartu dihapus (wishlist.js menghapus kartu)
  function watchList(listId, counterId, emptyId) {
    const list = document.getElementById(listId);
    if (!list) return;
    const counter = document.getElementById(counterId);
    const empty = document.getElementById(emptyId);
    new MutationObserver(() => {
      const total = list.querySelectorAll('[data-wishlist-card]').length;
      if (counter) counter.textContent = total;
      if (empty) empty.hidden = total > 0;
    }).observe(list, { childList: true });
  }

  watchList('ms-wishlist-list', 'mw-merchant-count', 'ms-wishlist-empty');
  watchList('sb-wishlist-list', 'mw-bag-count', 'sb-wishlist-empty');

  // ?tab=bags membuka tab Surprise Bags langsung
  selectTab(new URLSearchParams(window.location.search).get('tab') === 'bags' ? 'bags' : 'merchants');
})();
