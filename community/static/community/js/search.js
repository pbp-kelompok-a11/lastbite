const searchForm = document.querySelector('.community-search');

if (searchForm) {
  const input = searchForm.querySelector('[name="q"]');
  const category = searchForm.querySelector('[name="post_type"]');
  const tabs = document.querySelector('.community-tabs');
  const status = document.getElementById('community-search-status');
  const heading = document.getElementById('food-hacks-title');
  let results = document.getElementById('community-results');
  let timer;
  let statusTimer;
  let controller;
  let sequence = 0;

  function cancelPending() {
    window.clearTimeout(timer);
    window.clearTimeout(statusTimer);
    controller?.abort();
    sequence += 1;
    results.removeAttribute('aria-busy');
  }

  function makeUrl(postType = category.value, page = 1) {
    const url = new URL(searchForm.action);
    url.searchParams.set('post_type', postType);
    const query = input.value.trim();
    if (query) url.searchParams.set('q', query);
    if (page > 1) url.searchParams.set('page', page);
    return url;
  }

  async function search(page = 1, scrollToResults = false) {
    cancelPending();
    const current = sequence;
    controller = new AbortController();
    const url = makeUrl(category.value, page);
    const query = input.value.trim();
    const postType = category.value;
    results.setAttribute('aria-busy', 'true');
    status.textContent = 'Mencari postingan…';
    status.hidden = false;
    try {
      const response = await fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        signal: controller.signal,
        credentials: 'same-origin',
        mode: 'same-origin',
      });
      if (!response.ok) throw new Error('Search failed');
      const html = await response.text();
      if (current !== sequence) return;
      const documentFragment = new DOMParser().parseFromString(html, 'text/html');
      const updated = documentFragment.getElementById('community-results');
      if (!updated) throw new Error('Missing search results');
      results.replaceWith(updated);
      results = updated;
      const actualPage = Number(results.dataset.page);
      if (actualPage > 1) url.searchParams.set('page', actualPage);
      else url.searchParams.delete('page');
      heading.textContent = query ? 'Hasil pencarian' : postType === 'food_hack' ? 'Food Hacks terbaru' : 'Postingan terbaru';
      tabs.querySelectorAll('a').forEach((tab) => {
        const type = new URL(tab.href).searchParams.get('post_type');
        const active = type === postType;
        tab.classList.toggle('community-tab--active', active);
        if (active) tab.setAttribute('aria-current', 'page');
        else tab.removeAttribute('aria-current');
        tab.href = makeUrl(type).href;
      });
      window.history.replaceState(null, '', url);
      if (scrollToResults) {
        results.querySelector('.community-page--current')?.focus({ preventScroll: true });
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        results.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
      }
      status.textContent = 'Hasil pencarian diperbarui.';
      statusTimer = window.setTimeout(() => {
        status.hidden = true;
      }, 1000);
    } catch (error) {
      if (error.name === 'AbortError' || current !== sequence) return;
      status.textContent = 'Pencarian gagal. Hasil sebelumnya tetap ditampilkan. Tekan Cari untuk mencoba lagi.';
    } finally {
      if (current === sequence) results.removeAttribute('aria-busy');
    }
  }

  function debounceSearch() {
    cancelPending();
    status.hidden = true;
    timer = window.setTimeout(search, 350);
  }

  input.addEventListener('input', (event) => {
    if (!event.isComposing) debounceSearch();
  });
  input.addEventListener('compositionstart', cancelPending);
  input.addEventListener('compositionend', debounceSearch);
  searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    search();
  });

  function isPlainClick(event) {
    return event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;
  }

  tabs.addEventListener('click', (event) => {
    const tab = event.target.closest('a');
    if (!tab || !isPlainClick(event)) return;
    event.preventDefault();
    category.value = new URL(tab.href).searchParams.get('post_type');
    search();
  });

  document.getElementById('community-results').parentElement.addEventListener('click', (event) => {
    const pageLink = event.target.closest('[data-page-link]');
    if (pageLink && isPlainClick(event)) {
      event.preventDefault();
      search(Number(pageLink.dataset.pageLink), true);
      return;
    }
    if (!event.target.closest('[data-clear-search]') || !isPlainClick(event)) return;
    event.preventDefault();
    input.value = '';
    search();
    input.focus();
  });
}
