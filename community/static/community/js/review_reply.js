const reviewReplyDialog = document.getElementById('review-reply-dialog');

if (reviewReplyDialog) {
  const opener = document.getElementById('review-reply-open');
  function openReviewReply() {
    if (!reviewReplyDialog.open) reviewReplyDialog.showModal();
    reviewReplyDialog.querySelector('textarea').focus();
  }
  opener.addEventListener('click', openReviewReply);
  reviewReplyDialog.querySelectorAll('[data-review-reply-close]').forEach((button) => {
    button.addEventListener('click', () => reviewReplyDialog.close());
  });
  reviewReplyDialog.addEventListener('close', () => opener.focus());
  if (reviewReplyDialog.dataset.openOnLoad === 'true') openReviewReply();
}
