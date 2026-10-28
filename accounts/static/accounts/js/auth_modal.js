/**  Auth Modal Overlay */
document.addEventListener('DOMContentLoaded', function () {
  const overlay = document.getElementById('auth-overlay');
  if (!overlay) return;

  const closeBtn = document.getElementById('auth-modal-close');
  const backdrop = document.getElementById('auth-overlay-backdrop');

  // Panels
  const panels = {
    login: document.getElementById('auth-panel-login'),
    register: document.getElementById('auth-panel-register'),
    forgot: document.getElementById('auth-panel-forgot'),
    newpass: document.getElementById('auth-panel-newpass'),
  };

  function switchAuthPanel(panelName) {
    Object.keys(panels).forEach(function (name) {
      if (panels[name]) {
        panels[name].classList.toggle('is-active', name === panelName);
      }
    });

    // Clear error messages when switching panels
    ['auth-login-errors', 'auth-register-errors', 'auth-forgot-errors', 'auth-newpass-errors'].forEach(function (id) {
      const errEl = document.getElementById(id);
      if (errEl) {
        errEl.hidden = true;
        errEl.innerHTML = '';
      }
    });

    // Auto-focus first input
    const activePanel = panels[panelName];
    if (activePanel) {
      const firstInput = activePanel.querySelector('input:not([type="hidden"])');
      if (firstInput) setTimeout(() => firstInput.focus(), 60);
    }
  }

  function openAuthModal(panelName = 'login', role = 'customer') {
    switchAuthPanel(panelName);
    if (panelName === 'register') {
      selectRegisterRole(role);
    }
    overlay.hidden = false;
    document.body.classList.add('auth-modal-open');
  }

  function closeAuthModal() {
    overlay.hidden = true;
    document.body.classList.remove('auth-modal-open');
  }

  // Expose to window for external triggers
  window.openAuthModal = openAuthModal;
  window.closeAuthModal = closeAuthModal;
  window.switchAuthPanel = switchAuthPanel;

  // Close triggers
  if (closeBtn) closeBtn.addEventListener('click', closeAuthModal);
  if (backdrop) backdrop.addEventListener('click', closeAuthModal);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !overlay.hidden) {
      closeAuthModal();
    }
  });

  // Switch triggers inside modal
  const toRegisterBtn = document.getElementById('auth-to-register-btn');
  const toLoginBtn = document.getElementById('auth-to-login-btn');
  const toForgotBtn = document.getElementById('auth-to-forgot-btn');
  const forgotBackBtn = document.getElementById('auth-forgot-back-btn');
  const newpassBackBtn = document.getElementById('auth-newpass-back-btn');

  if (toRegisterBtn) toRegisterBtn.addEventListener('click', () => switchAuthPanel('register'));
  if (toLoginBtn) toLoginBtn.addEventListener('click', () => switchAuthPanel('login'));
  if (toForgotBtn) toForgotBtn.addEventListener('click', () => switchAuthPanel('forgot'));
  if (forgotBackBtn) forgotBackBtn.addEventListener('click', () => switchAuthPanel('login'));
  if (newpassBackBtn) newpassBackBtn.addEventListener('click', () => switchAuthPanel('login'));

  // Role selector in register form
  const tabCustomer = document.getElementById('modal-tab-customer');
  const tabMerchant = document.getElementById('modal-tab-merchant');
  const roleInput = document.getElementById('modal-register-role');
  const registerSubmit = document.getElementById('modal-register-submit');

  function selectRegisterRole(role) {
    const isCustomer = role !== 'merchant';
    if (tabCustomer) {
      tabCustomer.classList.toggle('is-active', isCustomer);
      tabCustomer.setAttribute('aria-pressed', isCustomer ? 'true' : 'false');
    }
    if (tabMerchant) {
      tabMerchant.classList.toggle('is-active', !isCustomer);
      tabMerchant.setAttribute('aria-pressed', !isCustomer ? 'true' : 'false');
    }
    if (roleInput) roleInput.value = isCustomer ? 'customer' : 'merchant';
    if (registerSubmit) {
      registerSubmit.textContent = isCustomer ? 'Daftar sebagai Customer' : 'Daftar sebagai Merchant';
    }
  }

  if (tabCustomer) tabCustomer.addEventListener('click', () => selectRegisterRole('customer'));
  if (tabMerchant) tabMerchant.addEventListener('click', () => selectRegisterRole('merchant'));

  // Global link interception: any link to accounts:login or accounts:register opens modal
  document.addEventListener('click', function (e) {
    const link = e.target.closest('a');
    if (!link) return;

    const href = link.getAttribute('href');
    if (!href) return;

    if (href.includes('/accounts/login')) {
      e.preventDefault();
      openAuthModal('login');
    } else if (href.includes('/accounts/register')) {
      e.preventDefault();
      const role = href.includes('role=merchant') ? 'merchant' : 'customer';
      openAuthModal('register', role);
    }
  });

  // URL query param trigger (e.g., /?auth=login)
  const urlParams = new URLSearchParams(window.location.search);
  const authAction = urlParams.get('auth');
  if (authAction === 'login' || authAction === 'register' || authAction === 'forgot') {
    const roleParam = urlParams.get('role') || 'customer';
    openAuthModal(authAction, roleParam);
    const cleanUrl = window.location.pathname;
    window.history.replaceState({}, document.title, cleanUrl);
  }

  // Helper to render error messages
  function renderErrors(container, errors) {
    if (!container) return;
    let html = '<ul>';
    if (typeof errors === 'string') {
      html += `<li>${errors}</li>`;
    } else if (Array.isArray(errors)) {
      errors.forEach(err => html += `<li>${err}</li>`);
    } else if (typeof errors === 'object') {
      Object.entries(errors).forEach(([field, msgs]) => {
        const fieldLabel = field === '__all__' ? '' : `<strong>${field}:</strong> `;
        if (Array.isArray(msgs)) {
          msgs.forEach(m => html += `<li>${fieldLabel}${m}</li>`);
        } else {
          html += `<li>${fieldLabel}${msgs}</li>`;
        }
      });
    }
    html += '</ul>';
    container.innerHTML = html;
    container.hidden = false;
  }

  // 1. AJAX Login Form
  const loginForm = document.getElementById('auth-login-form');
  const loginErrors = document.getElementById('auth-login-errors');
  const loginSubmit = document.getElementById('modal-login-submit');

  if (loginForm) {
    loginForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      loginErrors.hidden = true;
      loginSubmit.disabled = true;
      loginSubmit.textContent = 'Memproses...';

      try {
        const formData = new FormData(loginForm);
        const res = await fetch(loginForm.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          body: formData,
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          window.location.reload();
        } else {
          renderErrors(loginErrors, data.errors || 'Username atau kata sandi salah. Silakan coba lagi.');
        }
      } catch (err) {
        renderErrors(loginErrors, 'Terjadi kendala jaringan. Silakan coba lagi.');
      } finally {
        loginSubmit.disabled = false;
        loginSubmit.textContent = 'Masuk';
      }
    });
  }

  // 2. AJAX Register Form
  const registerForm = document.getElementById('auth-register-form');
  const registerErrors = document.getElementById('auth-register-errors');

  if (registerForm) {
    registerForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      registerErrors.hidden = true;
      registerSubmit.disabled = true;
      const originalText = registerSubmit.textContent;
      registerSubmit.textContent = 'Mendaftarkan...';

      try {
        const formData = new FormData(registerForm);
        const res = await fetch(registerForm.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          body: formData,
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          switchAuthPanel('login');
          loginErrors.hidden = false;
          loginErrors.className = 'notification notification--success';
          loginErrors.style.marginBottom = '1rem';
          loginErrors.innerHTML = '<p>Akun berhasil dibuat! Silakan masuk dengan akun barumu.</p>';
        } else {
          renderErrors(registerErrors, data.errors || 'Gagal mendaftar. Periksa kembali isian formulir.');
        }
      } catch (err) {
        renderErrors(registerErrors, 'Terjadi kendala jaringan. Silakan coba lagi.');
      } finally {
        registerSubmit.disabled = false;
        registerSubmit.textContent = originalText;
      }
    });
  }

  // 3. Step 2 & 3: Masukkan Email -> Validasi Django
  const forgotForm = document.getElementById('auth-forgot-form');
  const forgotErrors = document.getElementById('auth-forgot-errors');
  const forgotSubmit = document.getElementById('modal-forgot-submit');
  const verifiedUserEl = document.getElementById('reset-verified-user');

  if (forgotForm) {
    forgotForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      forgotErrors.hidden = true;
      forgotSubmit.disabled = true;
      forgotSubmit.textContent = 'Memvalidasi...';

      try {
        const formData = new FormData(forgotForm);
        const res = await fetch(forgotForm.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          body: formData,
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          // User found in database! Proceed to Step 4: Form password baru
          if (verifiedUserEl) verifiedUserEl.textContent = data.display_name || data.username || '';
          switchAuthPanel('newpass');
        } else {
          renderErrors(forgotErrors, data.error || 'Pengguna dengan email/username tersebut tidak ditemukan.');
        }
      } catch (err) {
        renderErrors(forgotErrors, 'Terjadi kesalahan sistem. Silakan coba lagi.');
      } finally {
        forgotSubmit.disabled = false;
        forgotSubmit.textContent = 'Verifikasi & Lanjut';
      }
    });
  }

  // 4. Step 4 & 5: Form Password Baru -> Django Menyimpan Perubahan
  const newpassForm = document.getElementById('auth-newpass-form');
  const newpassErrors = document.getElementById('auth-newpass-errors');
  const newpassSubmit = document.getElementById('modal-newpass-submit');
  const loginUsernameInput = document.getElementById('modal-login-username');

  if (newpassForm) {
    newpassForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      newpassErrors.hidden = true;
      newpassSubmit.disabled = true;
      newpassSubmit.textContent = 'Menyimpan...';

      try {
        const formData = new FormData(newpassForm);
        const res = await fetch(newpassForm.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          body: formData,
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          // Password saved successfully! Step 6: Kembali ke login
          switchAuthPanel('login');
          if (loginUsernameInput && data.username) {
            loginUsernameInput.value = data.username;
          }
          loginErrors.hidden = false;
          loginErrors.className = 'notification notification--success';
          loginErrors.style.marginBottom = '1rem';
          loginErrors.innerHTML = '<p>Kata sandi berhasil diubah! Silakan masuk menggunakan kata sandi barumu.</p>';
        } else {
          renderErrors(newpassErrors, data.error || 'Gagal menyimpan kata sandi. Pastikan kedua kata sandi cocok.');
        }
      } catch (err) {
        renderErrors(newpassErrors, 'Terjadi kendala jaringan. Silakan coba lagi.');
      } finally {
        newpassSubmit.disabled = false;
        newpassSubmit.textContent = 'Simpan Perubahan & Masuk';
      }
    });
  }
});
