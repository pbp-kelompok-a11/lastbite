// Simpan ID postingan yang sedang diproses agar like tidak terkirim ganda.
const pendingUpvotes = new Set();

// Kirim perubahan like untuk postingan yang tombolnya ditekan.
async function submitPostLike(event) {
  const form = event.target.closest('[data-upvote-form]');
  if (!form) {
    return;
  }
  event.preventDefault();
  const widget = form.closest('[data-upvote-post]');

  const postId = widget.dataset.upvotePost;
  if (pendingUpvotes.has(postId)) {
    return;
  }
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
    let data = {};
    if (response.headers.get('Content-Type')?.includes('application/json')) {
      data = await response.json();
    }
    if (response.status === 401 && data.login_url) {
      window.location.assign(data.login_url);
      return;
    }
    if (!response.ok) {
      throw new Error(data.error || 'Like gagal. Muat ulang halaman lalu coba lagi.');
    }

    // Samakan jumlah dan status like pada semua tampilan postingan yang sama.
    document.querySelectorAll(`[data-upvote-post="${postId}"]`).forEach((item) => {
      item.querySelector('[data-upvote-count]').textContent = data.upvote_count;
      const currentButton = item.querySelector('button');
      if (currentButton) {
        currentButton.setAttribute('aria-pressed', String(data.has_upvoted));
        currentButton.classList.toggle('community-upvote__button--active', data.has_upvoted);
      }
    });

    // Beri tahu feed jika hasil perlu diurutkan atau difilter ulang.
    document.dispatchEvent(new CustomEvent('community:like-changed'));
  } catch (error) {
    errorMessage.textContent = error.name === 'TypeError'
      ? 'Koneksi gagal. Periksa koneksi lalu coba lagi.' : error.message;
    errorMessage.hidden = false;

  // Aktifkan kembali tombol, baik request berhasil maupun gagal.
  } finally {
    pendingUpvotes.delete(postId);
    button.disabled = false;
    button.removeAttribute('aria-busy');
  }
}

document.addEventListener('submit', submitPostLike);
