(() => {
  const root = document.querySelector('.ms-store-detail-page');
  const ratingBar = document.getElementById('ms-store-rating');

  if (!root || !ratingBar) return;

  const feedback = document.getElementById('ms-rating-feedback');
  const summary = document.getElementById('ms-profile-rating-summary');

  const getStars = () =>
    Array.from(ratingBar.querySelectorAll('.js-store-rate'));

  function updateStars(selectedRating) {
    getStars().forEach((button) => {
      const value = Number(button.dataset.rating);

      button.classList.toggle(
        'is-filled',
        value <= selectedRating
      );

      button.setAttribute(
        'aria-pressed',
        value === selectedRating ? 'true' : 'false'
      );
    });
  }

  document.addEventListener('click', async (event) => {
    const button = event.target.closest('.js-store-rate');

    if (
      !button ||
      !ratingBar.contains(button) ||
      button.disabled
    ) {
      return;
    }

    const selectedRating = Number(button.dataset.rating);
    const buttons = getStars();
    const csrfToken = root.dataset.csrf || '';

    if (selectedRating < 1 || selectedRating > 5) return;

    buttons.forEach((item) => {
      item.disabled = true;
    });

    if (feedback) {
      feedback.textContent = 'Menyimpan rating...';
      feedback.classList.remove('is-error');
    }

    try {
      const response = await fetch(ratingBar.dataset.rateUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json',
          'Content-Type':
            'application/x-www-form-urlencoded;charset=UTF-8',
        },
        body: new URLSearchParams({
          rating: String(selectedRating),
        }).toString(),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.error || 'Gagal menyimpan rating. Silakan coba lagi.'
        );
      }

      // Tampilkan rating pilihan customer.
      ratingBar.dataset.userRating = String(data.user_rating);
      updateStars(Number(data.user_rating));

      // Perbarui rata-rata dan jumlah rating di bagian atas.
      if (summary) {
        const average = Number(data.average);

        summary.textContent =
          `Rating ${average.toFixed(1)}/5 (${data.count} rating)`;
      }

      if (feedback) {
        feedback.textContent =
          data.message || 'Rating berhasil disimpan.';
        feedback.classList.remove('is-error');
      }

    } catch (error) {
      if (feedback) {
        feedback.textContent = error.message;
        feedback.classList.add('is-error');
      }

    } finally {
      buttons.forEach((item) => {
        item.disabled = false;
      });
    }
  });
})();
