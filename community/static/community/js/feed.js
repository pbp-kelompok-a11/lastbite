const searchForm = document.querySelector('.community-search');

if (searchForm) {
  const input = searchForm.querySelector('[name="q"]');
  const category = searchForm.querySelector('[name="post_type"]');
  const sort = document.getElementById('community-sort');
  const rating = document.getElementById('community-rating');
  const ratingFilter = document.querySelector('.community-rating-filter');
  const searchLabel = searchForm.querySelector('label[for="community-query"]');
  const liked = document.getElementById('community-liked');
  const mine = document.getElementById('community-mine');
  const mineFilter = document.querySelector('.community-mine-filter');
  const likedFilter = document.querySelector('.community-food-hack-filter');
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
    if (mine?.value === '1' && postType === 'all') url.searchParams.set('mine', '1');
    const query = input.value.trim();
    if (query) url.searchParams.set('q', query);
    if (sort.value !== 'newest' && postType === category.value) {
      url.searchParams.set('sort', sort.value);
    }
    if (liked.value === '1' && postType === 'food_hack') url.searchParams.set('liked', '1');
    if (postType === 'review' && rating.value !== 'all') url.searchParams.set('rating', rating.value);
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
      if (response.status === 401) {
        const data = await response.json();
        if (current !== sequence) return;
        if (data.login_url) window.location.assign(data.login_url);
        return;
      }
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
      heading.textContent = results.dataset.heading;
      if (mine) mine.value = results.dataset.mine;
      if (mineFilter) mineFilter.hidden = postType !== 'all';
      if (results.dataset.mine !== '1') url.searchParams.delete('mine');
      sort.replaceChildren(results.querySelector('#community-sort-options').content.cloneNode(true));
      sort.value = results.dataset.sort;
      if (sort.value === 'newest') url.searchParams.delete('sort');
      else url.searchParams.set('sort', sort.value);
      liked.value = results.dataset.liked;
      likedFilter.hidden = postType !== 'food_hack';
      if (liked.value !== '1') url.searchParams.delete('liked');
      rating.value = results.dataset.rating;
      ratingFilter.hidden = postType !== 'review';
      if (rating.value === 'all') url.searchParams.delete('rating');
      else url.searchParams.set('rating', rating.value);
      searchLabel.textContent = results.dataset.searchLabel;
      input.placeholder = results.dataset.searchPlaceholder;
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
  sort.addEventListener('change', () => search());
  rating.addEventListener('change', () => search());
  liked.addEventListener('change', () => search());
  mine?.addEventListener('change', () => search());
  document.addEventListener('community:like-changed', () => {
    if (liked.value === '1' || sort.value === 'likes') search(Number(results.dataset.page));
  });
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
    const nextCategory = new URL(tab.href).searchParams.get('post_type');
    if (nextCategory === category.value) return;
    category.value = nextCategory;
    if (mine) mine.value = '0';
    sort.value = 'newest';
    liked.value = '0';
    rating.value = 'all';
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
