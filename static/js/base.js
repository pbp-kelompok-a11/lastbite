// LastBite — Base JS

// === Navbar scroll effect ===
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    if (window.scrollY > 10) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });
}

// === Mobile hamburger menu ===
const hamburgerBtn = document.getElementById('hamburgerBtn');
const navLinks = document.getElementById('navLinks');
if (hamburgerBtn && navLinks) {
  hamburgerBtn.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    const isOpen = navLinks.classList.contains('open');
    hamburgerBtn.setAttribute('aria-expanded', isOpen);
  });
  // Close nav when a link is clicked
  navLinks.querySelectorAll('.navbar__link').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      hamburgerBtn.setAttribute('aria-expanded', false);
    });
  });
}
