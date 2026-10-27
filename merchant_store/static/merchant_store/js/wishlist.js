// Tombol wishlist (AJAX)
(() => {
  function setWishlistButtonState(button, wishlisted) {
    button.dataset.wishlisted = wishlisted ? 'true' : 'false';
    button.setAttribute('aria-pressed', wishlisted ? 'true' : 'false');
    if (button.hasAttribute('data-icon-only')) {
      button.textContent = wishlisted ? '♥' : '♡';
      const label = wishlisted ? 'Hapus dari wishlist' : 'Simpan ke wishlist';
      button.setAttribute('aria-label', label);
      button.title = label;
    } else {
      button.textContent = wishlisted ? '♥ Tersimpan' : '♡ Simpan';
    }
  }
  window.setWishlistButtonState = setWishlistButtonState;

  document.addEventListener('click', async (event) => {
    const button = event.target.closest('.js-wishlist-toggle');
    if (!button || button.disabled) return;

    const root = button.closest('[data-csrf]');
    const csrfToken = root ? root.dataset.csrf : '';
    const previousLabel = button.textContent;
    button.disabled = true;

    try {
      const response = await fetch(button.dataset.url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken, 'Accept': 'application/json' },
        credentials: 'same-origin',
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || 'Gagal memperbarui wishlist.');

      setWishlistButtonState(button, data.wishlisted);

      //Kartu hilang saat dihapus dari favorit
      if (!data.wishlisted && button.dataset.removeOnUnwish === 'true') {
        const card = button.closest('[data-wishlist-card]');
        if (card) card.remove();
        const list = document.getElementById('ms-wishlist-list');
        const empty = document.getElementById('ms-wishlist-empty');
        if (list && empty && !list.querySelector('[data-wishlist-card]')) empty.hidden = false;
      }

    } catch (error) {
      if (button.hasAttribute('data-icon-only')) {
        button.title = 'Gagal, coba lagi';
      } else {
        button.textContent = 'Gagal, coba lagi';
        window.setTimeout(() => { button.textContent = previousLabel; }, 2000);
      }
    } finally {
      button.disabled = false;
    }
  });
})();
