const reviewForm = document.querySelector('.community-review-form');

if (reviewForm) {
  // Teks penilaian mengikuti bintang yang dipilih user.
  const ratingFeedback = document.getElementById('review-rating-feedback');
  const ratingDescriptions = ['Sangat kurang', 'Kurang', 'Cukup', 'Baik', 'Sangat baik'];

  // Pilihan kosong memakai petunjuk awal; pilihan terisi menampilkan deskripsi rating.
  function updateRating() {
    const selected = reviewForm.querySelector('[name="rating"]:checked');
    if (!selected) {
      ratingFeedback.textContent = 'Pilih bintang untuk memberi rating';
      return;
    }

    const rating = Number(selected.value);
    const description = ratingDescriptions[rating - 1];
    ratingFeedback.textContent = `${description} · ${selected.value} bintang`;
  }

  reviewForm.querySelectorAll('[name="rating"]').forEach((radio) => {
    radio.addEventListener('change', updateRating);
  });
  updateRating();

  // Setelah tersimpan, ganti form dengan pesan sukses dan tautan detail.
  function showReviewSuccess(data) {
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
  }

  // Gabungkan pesan validasi dari setiap field menjadi satu pesan.
  function getReviewErrorMessage(errors) {
    const messages = [];
    for (const fieldErrors of Object.values(errors || {})) {
      for (const error of fieldErrors) {
        messages.push(error.message);
      }
    }
    return messages.join(' ') || 'Review belum dapat disimpan. Coba kembali.';
  }

  // Cegah review terkirim dua kali saat menunggu respons.
  let submitting = false;

  // Kirim form dan tangani hasil simpan atau error validasi.
  async function submitReview(event) {
    event.preventDefault();
    if (submitting) {
      return;
    }
    const status = document.getElementById('review-submit-feedback');
    const submitButton = reviewForm.querySelector('[type="submit"]');
    submitting = true;
    submitButton.disabled = true;
    status.textContent = 'Menyimpan review...';

    try {
      const response = await fetch(reviewForm.action, {
        method: 'POST',
        body: new FormData(reviewForm),
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        credentials: 'same-origin',
        mode: 'same-origin',
      });

      // Ikuti redirect server, misalnya ketika sesi login sudah berakhir.
      if (response.redirected) {
        window.location.assign(response.url);
        return;
      }
      if (!response.headers.get('content-type')?.includes('application/json')) {
        throw new Error('Review belum dapat disimpan. Periksa sesi login lalu coba kembali.');
      }

      const data = await response.json();
      if (!response.ok) {
        throw new Error(getReviewErrorMessage(data.errors));
      }
      showReviewSuccess(data);
    } catch (error) {
      status.textContent = error.message;
      submitting = false;
      submitButton.disabled = false;
    }
  }

  reviewForm.addEventListener('submit', submitReview);
}
