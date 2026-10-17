const pendingUpvotes = new Set();

document.addEventListener('submit', async (event) => {
  const form = event.target.closest('[data-upvote-form]');
  if (!form) return;
  event.preventDefault();
  const widget = form.closest('[data-upvote-post]');
  const postId = widget.dataset.upvotePost;
  if (pendingUpvotes.has(postId)) return;
  const button = form.querySelector('button');
  const errorMessage = widget.querySelector('[data-upvote-error]');
  pendingUpvotes.add(postId);
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  errorMessage.hidden = true;
  try {
    const response = await fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
      mode: 'same-origin',
    });
    const data = response.headers.get('Content-Type')?.includes('application/json')
      ? await response.json() : {};
    if (response.status === 401 && data.login_url) {
      window.location.assign(data.login_url);
      return;
    }
    if (!response.ok) throw new Error(data.error || 'Like gagal. Muat ulang halaman lalu coba lagi.');
    document.querySelectorAll(`[data-upvote-post="${postId}"]`).forEach((item) => {
      item.querySelector('[data-upvote-count]').textContent = data.upvote_count;
      const currentButton = item.querySelector('button');
      if (currentButton) {
        currentButton.setAttribute('aria-pressed', String(data.has_upvoted));
        currentButton.classList.toggle('community-upvote__button--active', data.has_upvoted);
        currentButton.querySelector('[data-like-label]').textContent = data.has_upvoted ? 'Liked' : 'Like';
      }
    });
    document.dispatchEvent(new CustomEvent('community:like-changed'));
  } catch (error) {
    errorMessage.textContent = error.name === 'TypeError'
      ? 'Koneksi gagal. Periksa koneksi lalu coba lagi.' : error.message;
    errorMessage.hidden = false;
  } finally {
    pendingUpvotes.delete(postId);
    button.disabled = false;
    button.removeAttribute('aria-busy');
  }
});
