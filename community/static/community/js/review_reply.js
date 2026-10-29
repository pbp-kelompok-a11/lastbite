const reviewReplyDialog = document.getElementById('review-reply-dialog');

if (reviewReplyDialog) {
  const replyButton = document.getElementById('review-reply-open');

  // Buka form balasan Merchant dan arahkan fokus ke textarea.
  function openReviewReply() {
    if (!reviewReplyDialog.open) {
      reviewReplyDialog.showModal();
    }
    reviewReplyDialog.querySelector('textarea').focus();
  }

  // Tombol buka/tutup hanya mengatur dialog; penyimpanan memakai form POST biasa.
  replyButton.addEventListener('click', openReviewReply);
  reviewReplyDialog.querySelectorAll('[data-review-reply-close]').forEach((button) => {
    button.addEventListener('click', () => reviewReplyDialog.close());
  });
  reviewReplyDialog.addEventListener('close', () => replyButton.focus());

  // Jika validasi gagal, tampilkan kembali dialog beserta pesan error server.
  if (reviewReplyDialog.dataset.openOnLoad === 'true') {
    openReviewReply();
  }
}
