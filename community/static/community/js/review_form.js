const reviewForm = document.querySelector('.community-review-form');

if (reviewForm) {
  const feedback = document.getElementById('review-rating-feedback');
  const descriptions = ['Sangat kurang', 'Kurang', 'Cukup', 'Baik', 'Sangat baik'];
  function updateRating() {
    const selected = reviewForm.querySelector('[name="rating"]:checked');
    feedback.textContent = selected
      ? `${descriptions[Number(selected.value) - 1]} · ${selected.value} bintang`
      : 'Pilih bintang untuk memberi rating';
  }
  reviewForm.querySelectorAll('[name="rating"]').forEach((radio) => {
    radio.addEventListener('change', updateRating);
  });
  updateRating();

  let submitting = false;
  reviewForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (submitting) return;
    const status = document.getElementById('review-submit-feedback');
    const submit = reviewForm.querySelector('[type="submit"]');
    submitting = true;
    submit.disabled = true;
    status.textContent = 'Menyimpan review...';
    try {
      const response = await fetch(reviewForm.action, {
        method: 'POST', body: new FormData(reviewForm),
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        credentials: 'same-origin', mode: 'same-origin',
      });
      if (response.redirected) {
        window.location.assign(response.url);
        return;
      }
      if (!response.headers.get('content-type')?.includes('application/json')) {
        throw new Error('Review belum dapat disimpan. Periksa sesi login lalu coba kembali.');
      }
      const data = await response.json();
      if (!response.ok) {
        throw new Error(Object.values(data.errors || {}).flat().map(error => error.message).join(' ')
          || 'Review belum dapat disimpan. Coba kembali.');
      }
      const result = document.createElement('div');
      result.className = 'community-form';
      result.setAttribute('role', 'status');
      const message = document.createElement('p');
      message.textContent = data.message;
      const link = document.createElement('a');
      link.className = 'btn btn--primary btn--md';
      link.href = data.detail_url;
      link.textContent = 'Lihat Review';
      result.append(message, link);
      reviewForm.replaceWith(result);
      link.focus();
    } catch (error) {
      status.textContent = error.message;
      submitting = false;
      submit.disabled = false;
    }
  });
}
