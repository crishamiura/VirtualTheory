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
