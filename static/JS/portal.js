/* ─── portal.js ─── Global portal utilities ─── */

// ── CSRF Helper ──
function getCsrf() {
  return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
         document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

async function apiPost(url, data) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify(data)
  });
  return resp.json();
}

async function apiGet(url) {
  const resp = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' }
  });
  return resp.json();
}

// ── Toast ──
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span class="toast-msg">${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'fadeOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Modal ──
function openModal(id) { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('open');
  if (e.target.classList.contains('modal-close')) e.target.closest('.modal-overlay')?.classList.remove('open');
});

// ── Sidebar nav ──
function initSidebarNav() {
  const navItems = document.querySelectorAll('.nav-item[data-section]');
  const sections = document.querySelectorAll('.portal-section');

  function activateSection(sectionId) {
    sections.forEach(s => s.classList.remove('active'));
    navItems.forEach(n => n.classList.remove('active'));
    const target = document.getElementById(sectionId);
    const navItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
    if (target) target.classList.add('active');
    if (navItem) navItem.classList.add('active');
    document.getElementById('page-title').textContent = navItem?.dataset.title || 'Dashboard';
    document.getElementById('page-subtitle').textContent = navItem?.dataset.subtitle || '';
    // Update URL hash
    history.pushState(null, null, '#' + sectionId);
    // Trigger resize to fix FullCalendar rendering in hidden divs
    setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      activateSection(item.dataset.section);
      // Close sidebar on mobile
      if (window.innerWidth <= 900) toggleSidebar(false);
    });
  });

  // Load from hash or default
  const hash = location.hash.replace('#', '');
  const defaultSection = navItems[0]?.dataset.section;
  activateSection(hash && document.getElementById(hash) ? hash : defaultSection);
}

// ── Sidebar mobile ──
function toggleSidebar(force) {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');
  const isOpen = typeof force === 'boolean' ? force : !sidebar.classList.contains('open');
  sidebar.classList.toggle('open', isOpen);
  overlay.classList.toggle('open', isOpen);
}
document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('.hamburger')?.addEventListener('click', () => toggleSidebar());
  document.querySelector('.sidebar-overlay')?.addEventListener('click', () => toggleSidebar(false));
});

// ── Theme Toggle ──
function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeBtn(saved);
}
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateThemeBtn(next);
}
function updateThemeBtn(theme) {
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = theme === 'dark' ? 'Light appearance' : 'Dark appearance';
}

// ── BMI Calculator ──
function calcBMI(height_cm, weight_kg) {
  if (!height_cm || !weight_kg) return null;
  const h = height_cm / 100;
  const bmi = (weight_kg / (h * h)).toFixed(1);
  let label = '';
  if (bmi < 18.5) label = 'Underweight';
  else if (bmi < 25) label = 'Normal';
  else if (bmi < 30) label = 'Overweight';
  else label = 'Obese';
  return { bmi, label };
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSidebarNav();
});
