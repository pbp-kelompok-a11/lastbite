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
}
