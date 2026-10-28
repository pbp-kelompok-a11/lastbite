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

  // jumlah di tab Merchant ikut berkurang saat kartu dihapus (wishlist.js menghapus kartu)
  const list = document.getElementById('ms-wishlist-list');
  const counter = document.getElementById('mw-merchant-count');
  if (list && counter) {
    new MutationObserver(() => {
      counter.textContent = list.querySelectorAll('[data-wishlist-card]').length;
    }).observe(list, { childList: true });
  }

  selectTab('merchants');
})();