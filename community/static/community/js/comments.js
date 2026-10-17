let commentRequestPending = false;
let commentStatusTimer;

function revealCommentThread(element) {
  let thread = element?.parentElement.closest('[data-comment-thread]');
  while (thread) {
    thread.open = true;
    thread = thread.parentElement.closest('[data-comment-thread]');
  }
}

function openCommentDialog(dialog) {
  if (!dialog || dialog.open) return;
  revealCommentThread(dialog);
  dialog.showModal();
  const target = dialog.querySelector('[aria-invalid="true"], textarea');
  target?.focus();
}

function openInvalidCommentDialog(section = document) {
  openCommentDialog(section.querySelector('[data-comment-dialog][data-open-on-load="true"]'));
}

function closeCommentMenus(except = null) {
  document.querySelectorAll('[data-comment-menu-toggle]').forEach((toggle) => {
    if (toggle === except) return;
    toggle.setAttribute('aria-expanded', 'false');
    document.getElementById(toggle.getAttribute('aria-controls')).hidden = true;
  });
}

openInvalidCommentDialog();
document.addEventListener('click', (event) => {
  const menuToggle = event.target.closest('[data-comment-menu-toggle]');
  if (menuToggle) {
    const expanded = menuToggle.getAttribute('aria-expanded') === 'true';
    closeCommentMenus(menuToggle);
    menuToggle.setAttribute('aria-expanded', String(!expanded));
    document.getElementById(menuToggle.getAttribute('aria-controls')).hidden = expanded;
    return;
  }
  const opener = event.target.closest('[data-comment-dialog-open]');
  if (opener) {
    const dialog = document.getElementById(opener.dataset.commentDialogOpen);
    const returnFocus = opener.closest('.community-comment-menu')?.querySelector('[data-comment-menu-toggle]');
    if (returnFocus) dialog.dataset.returnFocus = returnFocus.id;
    closeCommentMenus();
    const error = dialog?.querySelector('[data-comment-dialog-status]');
    if (error) error.hidden = true;
    openCommentDialog(dialog);
  }
  if (!event.target.closest('.community-comment-menu')) closeCommentMenus();
  if (event.target.closest('[data-comment-dialog-close]') && !commentRequestPending) {
    event.target.closest('dialog')?.close();
  }
});
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  const expanded = document.querySelector('[data-comment-menu-toggle][aria-expanded="true"]');
  if (expanded) {
    closeCommentMenus();
    expanded.focus();
    event.preventDefault();
  }
});
document.addEventListener('close', (event) => {
  const target = event.target;
  if (target.matches('[data-comment-dialog]') && target.dataset.returnFocus) {
    document.getElementById(target.dataset.returnFocus)?.focus({ preventScroll: true });
  }
}, true);
document.addEventListener('cancel', (event) => {
  if (event.target.matches('[data-comment-dialog]') && commentRequestPending) event.preventDefault();
}, true);

document.addEventListener('submit', async (event) => {
  const form = event.target.closest('[data-comment-form]');
  if (!form) return;
  event.preventDefault();
  if (commentRequestPending) return;
  commentRequestPending = true;
  const section = form.closest('#comments');
  const body = new FormData(form);
  const action = form.dataset.commentForm;
  const commentId = form.dataset.commentId;
  const buttons = section.querySelectorAll('button');
  buttons.forEach((button) => { button.disabled = true; });
  section.setAttribute('aria-busy', 'true');
  const status = form.closest('dialog')?.querySelector('[data-comment-dialog-status]') || section.querySelector('[data-comment-status]');
  window.clearTimeout(commentStatusTimer);
  status.hidden = true;
  try {
    const response = await fetch(form.action, {
      method: 'POST', body,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin', mode: 'same-origin',
    });
    if (response.status === 401) {
      const data = await response.json();
      if (data.login_url) window.location.assign(data.login_url);
      return;
    }
    if (!response.ok && response.status !== 400) throw new Error('Komentar gagal diproses. Muat ulang halaman lalu coba lagi.');
    const html = await response.text();
    const updated = new DOMParser().parseFromString(html, 'text/html').getElementById('comments');
    if (!updated) throw new Error('Komentar gagal diperbarui. Silakan coba lagi.');
    section.querySelectorAll('textarea').forEach((textarea) => {
      if (form.contains(textarea)) return;
      const replacement = updated.querySelector(`#${textarea.id}`);
      if (replacement) replacement.value = textarea.value;
    });
    section.querySelectorAll('[data-comment-thread][open]').forEach((thread) => {
      const replacement = updated.querySelector(`#${thread.id}`);
      if (replacement) replacement.open = true;
    });
    section.querySelectorAll('dialog[open]').forEach((dialog) => { dialog.close(); });
    section.replaceWith(updated);
    document.querySelectorAll(`[data-post-comment-count="${updated.dataset.postId}"]`).forEach((count) => {
      count.textContent = updated.dataset.commentCount;
    });
    if (response.status === 400) {
      openInvalidCommentDialog(updated);
      updated.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }
    if (action !== 'like') {
      const feedback = updated.querySelector('[data-comment-status]');
      const messages = {
        create: 'Komentar berhasil dikirim.', reply: 'Balasan berhasil dikirim.',
        edit: 'Komentar berhasil diperbarui.', delete: 'Komentar berhasil dihapus.',
      };
      feedback.textContent = messages[action];
      feedback.hidden = false;
      commentStatusTimer = window.setTimeout(() => { feedback.hidden = true; }, 3000);
    }
    const target = action === 'create' || action === 'reply' ? updated.querySelector(`#comment-${updated.dataset.latestComment}`)
      : action === 'edit' ? updated.querySelector(`#comment-${commentId}`)
        : action === 'like' ? updated.querySelector(`#comment-${commentId} > .community-comment__actions [data-comment-form="like"] button`)
          : updated.querySelector('h2');
    revealCommentThread(target);
    target?.focus({ preventScroll: true });
  } catch (error) {
    status.textContent = error.name === 'TypeError' ? 'Koneksi gagal. Komentarmu tetap ada di kolom, silakan coba lagi.' : error.message;
    status.hidden = false;
  } finally {
    commentRequestPending = false;
    buttons.forEach((button) => { button.disabled = false; });
    section.removeAttribute('aria-busy');
  }
});

function focusCommentForm() {
  const target = document.querySelector('#comment-form textarea') || document.getElementById('comment-form');
  target?.focus({ preventScroll: true });
}

if (window.location.hash === '#comment-form') focusCommentForm();
window.addEventListener('load', () => {
  if (window.location.hash === '#comment-form') focusCommentForm();
}, { once: true });
window.addEventListener('hashchange', () => {
  if (window.location.hash === '#comment-form') focusCommentForm();
});
document.addEventListener('click', (event) => {
  if (!event.target.closest('[data-comment-link][href="#comment-form"]')) return;
  event.preventDefault();
  document.getElementById('comment-form')?.scrollIntoView({ block: 'start' });
  window.history.replaceState(null, '', '#comment-form');
  focusCommentForm();
});
