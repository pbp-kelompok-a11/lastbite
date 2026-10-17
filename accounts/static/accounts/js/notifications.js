document.querySelectorAll('.notification').forEach((notification) => {
  const timer = window.setTimeout(() => notification.remove(), 3000);
  notification.querySelector('.notification__close')?.addEventListener('click', () => {
    window.clearTimeout(timer);
    notification.remove();
  });
});
