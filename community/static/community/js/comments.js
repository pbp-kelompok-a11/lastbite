// Cegah dua aksi komentar dikirim bersamaan.
let commentRequestPending = false;
let commentStatusTimer;

// Buka semua induk balasan agar komentar tujuan terlihat.
function revealCommentThread(element) {
  let thread = element?.parentElement.closest('[data-comment-thread]');
  while (thread) {
    thread.open = true;
    thread = thread.parentElement.closest('[data-comment-thread]');
  }
}

// Buka dialog dan fokuskan input yang perlu diperbaiki atau diisi.
function openCommentDialog(dialog) {
  if (!dialog || dialog.open) {
    return;
  }
  revealCommentThread(dialog);
  dialog.showModal();

  const target = dialog.querySelector('[aria-invalid="true"], textarea');
  target?.focus();
}

// Tampilkan kembali dialog yang gagal validasi dari server.
function openInvalidCommentDialog(section = document) {
  openCommentDialog(section.querySelector('[data-comment-dialog][data-open-on-load="true"]'));
}

// Tutup menu lain saat satu menu komentar dibuka.
function closeCommentMenus(except = null) {
  document.querySelectorAll('[data-comment-menu-toggle]').forEach((toggle) => {
    if (toggle === except) {
      return;
    }
    toggle.setAttribute('aria-expanded', 'false');
    document.getElementById(toggle.getAttribute('aria-controls')).hidden = true;
  });
}

function preserveCommentState(section, updated, submittedForm) {
  // Jangan hilangkan draft lain dan balasan yang sedang dibuka.
  section.querySelectorAll('textarea').forEach((textarea) => {
    if (submittedForm.contains(textarea)) {
      return;
    }
    const replacement = updated.querySelector(`#${textarea.id}`);
    if (replacement) {
      replacement.value = textarea.value;
    }
  });
  section.querySelectorAll('[data-comment-thread][open]').forEach((thread) => {
    const replacement = updated.querySelector(`#${thread.id}`);
    if (replacement) {
      replacement.open = true;
    }
  });
}

// Pilih tujuan fokus sesuai aksi tambah, edit, like, atau hapus.
function getCommentFocusTarget(section, action, commentId) {
  if (action === 'create' || action === 'reply') {
    return section.querySelector(`#comment-${section.dataset.latestComment}`);
  }
  if (action === 'edit') {
    return section.querySelector(`#comment-${commentId}`);
  }
  if (action === 'like') {
    return section.querySelector(`#comment-${commentId} > .community-comment__actions [data-comment-form="like"] button`);
  }
  return section.querySelector('h2');
}

openInvalidCommentDialog();

// Tombol komentar mengatur menu serta dialog balas, edit, dan hapus.
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
    if (returnFocus) {
      dialog.dataset.returnFocus = returnFocus.id;
    }
    closeCommentMenus();
    const error = dialog?.querySelector('[data-comment-dialog-status]');
    if (error) {
      error.hidden = true;
    }
    openCommentDialog(dialog);
  }
  if (!event.target.closest('.community-comment-menu')) {
    closeCommentMenus();
  }
  if (event.target.closest('[data-comment-dialog-close]') && !commentRequestPending) {
    event.target.closest('dialog')?.close();
  }
});

// Escape menutup menu dan mengembalikan fokus ke tombolnya.
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') {
    return;
  }
  const expanded = document.querySelector('[data-comment-menu-toggle][aria-expanded="true"]');
  if (expanded) {
    closeCommentMenus();
    expanded.focus();
    event.preventDefault();
  }
});

// Kembalikan fokus setelah dialog ditutup.
document.addEventListener('close', (event) => {
  const target = event.target;
  if (target.matches('[data-comment-dialog]') && target.dataset.returnFocus) {
    document.getElementById(target.dataset.returnFocus)?.focus({ preventScroll: true });
  }
}, true);

// Dialog tidak boleh ditutup saat penyimpanan masih berlangsung.
document.addEventListener('cancel', (event) => {
  if (event.target.matches('[data-comment-dialog]') && commentRequestPending) {
    event.preventDefault();
  }
}, true);

// Satu alur POST untuk tambah, balas, edit, hapus, dan like komentar.
async function submitComment(event) {
  const form = event.target.closest('[data-comment-form]');
  if (!form) {
    return;
  }
  event.preventDefault();
  if (commentRequestPending) {
    return;
  }
  commentRequestPending = true;

  const section = form.closest('#comments');
  const body = new FormData(form);

  const action = form.dataset.commentForm;
  const commentId = form.dataset.commentId;

  // Nonaktifkan tombol selama request untuk mencegah pengiriman ganda.
  const buttons = section.querySelectorAll('button');
  buttons.forEach((button) => { button.disabled = true; });
  section.setAttribute('aria-busy', 'true');
  const status = form.closest('dialog')?.querySelector('[data-comment-dialog-status]') || section.querySelector('[data-comment-status]');
  window.clearTimeout(commentStatusTimer);
  status.hidden = true;

  try {
    const response = await fetch(form.action, {
      method: 'POST',
      body,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
      mode: 'same-origin',
    });
    if (response.status === 401) {
      const data = await response.json();
      if (data.login_url) {
        window.location.assign(data.login_url);
      }
      return;
    }
    if (!response.ok && response.status !== 400) {
      throw new Error('Komentar gagal diproses. Muat ulang halaman lalu coba lagi.');
    }

    const html = await response.text();
    const updated = new DOMParser().parseFromString(html, 'text/html').getElementById('comments');
    if (!updated) {
      throw new Error('Komentar gagal diperbarui. Silakan coba lagi.');
    }

    // Pertahankan draft lain sebelum mengganti daftar komentar.
    preserveCommentState(section, updated, form);
    section.querySelectorAll('dialog[open]').forEach((dialog) => { dialog.close(); });
    section.replaceWith(updated);
    document.querySelectorAll(`[data-post-comment-count="${updated.dataset.postId}"]`).forEach((count) => {
      count.textContent = updated.dataset.commentCount;
    });

    // Respons validasi berisi form dengan pesan error dari server.
    if (response.status === 400) {
      openInvalidCommentDialog(updated);
      updated.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }

    // Tampilkan pesan hasil untuk perubahan isi komentar.
    if (action !== 'like') {
      const feedback = updated.querySelector('[data-comment-status]');
      const messages = {
        create: 'Komentar berhasil dikirim.',
        reply: 'Balasan berhasil dikirim.',
        edit: 'Komentar berhasil diperbarui.',
        delete: 'Komentar berhasil dihapus.',
      };
      feedback.textContent = messages[action];
      feedback.hidden = false;
      commentStatusTimer = window.setTimeout(() => { feedback.hidden = true; }, 3000);
    }

    const target = getCommentFocusTarget(updated, action, commentId);
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
}

document.addEventListener('submit', submitComment);

// Arahkan user ke form komentar saat membuka tautan #comment-form.
function focusCommentForm() {
  const target = document.querySelector('#comment-form textarea') || document.getElementById('comment-form');
  target?.focus({ preventScroll: true });
}

if (window.location.hash === '#comment-form') {
  focusCommentForm();
}
window.addEventListener('load', () => {
  if (window.location.hash === '#comment-form') {
    focusCommentForm();
  }
}, { once: true });
window.addEventListener('hashchange', () => {
  if (window.location.hash === '#comment-form') {
    focusCommentForm();
  }
});
document.addEventListener('click', (event) => {
  if (!event.target.closest('[data-comment-link][href="#comment-form"]')) {
    return;
  }
  event.preventDefault();
  document.getElementById('comment-form')?.scrollIntoView({ block: 'start' });
  window.history.replaceState(null, '', '#comment-form');
  focusCommentForm();
});
