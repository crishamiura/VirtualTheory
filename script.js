// ===== Vital Theory — interactions =====

// Mobile nav toggle
const nav = document.getElementById('nav');
const navToggle = document.getElementById('navToggle');
navToggle?.addEventListener('click', () => nav.classList.toggle('open'));
document.querySelectorAll('.nav-links a').forEach(a =>
  a.addEventListener('click', () => nav.classList.remove('open'))
);

// FAQ accordion (single-open)
document.querySelectorAll('.faq-item').forEach(item => {
  const q = item.querySelector('.faq-q');
  const a = item.querySelector('.faq-a');
  q.addEventListener('click', () => {
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(other => {
      other.classList.remove('open');
      other.querySelector('.faq-a').style.maxHeight = null;
    });
    if (!isOpen) {
      item.classList.add('open');
      a.style.maxHeight = a.scrollHeight + 'px';
    }
  });
});

// Book: drag to rotate + click to "open" (bounce)
const book = document.getElementById('book');
if (book) {
  let dragging = false, startX = 0, rotY = -16;
  const setRot = y => { book.style.transform = `rotateY(${y}deg) rotateX(4deg)`; };
  book.addEventListener('pointerdown', e => { dragging = true; startX = e.clientX; book.style.cursor = 'grabbing'; book.style.transition = 'none'; });
  window.addEventListener('pointermove', e => {
    if (!dragging) return;
    const y = Math.max(-45, Math.min(25, rotY + (e.clientX - startX) * 0.35));
    setRot(y);
  });
  window.addEventListener('pointerup', e => {
    if (!dragging) return;
    dragging = false; book.style.cursor = 'grab'; book.style.transition = 'transform .5s ease';
    rotY = Math.max(-45, Math.min(25, rotY + (e.clientX - startX) * 0.35));
  });
  book.addEventListener('click', e => {
    if (Math.abs(e.clientX - startX) > 4) return; // ignore drags
    book.animate(
      [{ transform: book.style.transform || 'rotateY(-16deg) rotateX(4deg)' },
       { transform: 'rotateY(0deg) rotateX(0deg) scale(1.05)' },
       { transform: 'rotateY(-16deg) rotateX(4deg)' }],
      { duration: 700, easing: 'ease-in-out' }
    );
  });
}

// Subtle nav shadow on scroll
window.addEventListener('scroll', () => {
  nav.style.boxShadow = window.scrollY > 10 ? '0 4px 20px rgba(15,23,42,.06)' : 'none';
});

// ===== Scroll reveal: fade + ease in/out, re-triggers on enter AND exit =====
(function () {
  const root = document.documentElement;
  root.classList.add('reveal-on'); // gate: without JS, content stays visible
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const els = [];
  const reveal = (el, delay) => {
    el.classList.add('reveal');
    if (delay) el.style.transitionDelay = delay + 'ms';
    els.push(el);
  };

  // standalone blocks
  document.querySelectorAll(
    '.section-head, .hero-copy, .hero-book, .why-card, .about-copy, .price-card, .cta-box, .faq-item'
  ).forEach((el) => reveal(el, 0));

  // grids get a gentle stagger across their cards
  document.querySelectorAll('.cat-grid, .benefit-grid, .sample-grid, .test-grid')
    .forEach((grid) => {
      Array.from(grid.children).forEach((card, i) => reveal(card, (i % 5) * 70));
    });

  // Primary: IntersectionObserver toggles on enter AND exit
  let ioFired = false;
  const io = new IntersectionObserver((entries) => {
    ioFired = true;
    entries.forEach((e) => e.target.classList.toggle('in-view', e.isIntersecting));
  }, { threshold: 0.14, rootMargin: '0px 0px -8% 0px' });
  els.forEach((el) => io.observe(el));

  // Fallback: if IO never reports (rare/embedded viewers), use scroll math so
  // content is never stuck hidden — still toggles both ways.
  setTimeout(() => {
    if (ioFired) return;
    io.disconnect();
    const check = () => {
      const vh = window.innerHeight || document.documentElement.clientHeight;
      els.forEach((el) => {
        const r = el.getBoundingClientRect();
        el.classList.toggle('in-view', r.top < vh * 0.9 && r.bottom > vh * 0.08);
      });
    };
    check();
    addEventListener('scroll', check, { passive: true });
    addEventListener('resize', check, { passive: true });
  }, 1000);
})();
