/* AttendWise – Main JS */

// Sidebar toggle (mobile)
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('active');
    });
  }
  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('active');
    });
  }

  // Mark active nav link
  const links = document.querySelectorAll('.sidebar-nav .nav-link');
  links.forEach(link => {
    if (link.href === window.location.href) link.classList.add('active');
  });

  // Auto-dismiss alerts
  setTimeout(() => {
    document.querySelectorAll('.auto-dismiss').forEach(el => {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    });
  }, 4000);

  // Animate progress bars
  document.querySelectorAll('.att-progress-bar[data-width]').forEach(bar => {
    const w = bar.dataset.width;
    setTimeout(() => { bar.style.width = w + '%'; }, 100);
  });

  // Subject dropdown via AJAX
  const classSelect = document.getElementById('id_classroom');
  const subjectSelect = document.getElementById('id_subject');
  if (classSelect && subjectSelect) {
    classSelect.addEventListener('change', () => {
      const classId = classSelect.value;
      if (!classId) return;
      fetch(`/ajax/subjects-by-class/?classroom_id=${classId}`)
        .then(r => r.json())
        .then(data => {
          subjectSelect.innerHTML = '<option value="">-- Select Subject --</option>';
          data.subjects.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id; opt.textContent = s.name;
            subjectSelect.appendChild(opt);
          });
        });
    });
  }

  // Confirm delete
  document.querySelectorAll('.btn-delete-confirm').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
        e.preventDefault();
      }
    });
  });

  // Mark all present/absent buttons
  const markAllPresent = document.getElementById('markAllPresent');
  const markAllAbsent = document.getElementById('markAllAbsent');
  if (markAllPresent) {
    markAllPresent.addEventListener('click', () => {
      document.querySelectorAll('.status-radio[value="present"]').forEach(r => r.checked = true);
    });
  }
  if (markAllAbsent) {
    markAllAbsent.addEventListener('click', () => {
      document.querySelectorAll('.status-radio[value="absent"]').forEach(r => r.checked = true);
    });
  }

  // Search filter (client-side quick filter)
  const searchInput = document.getElementById('quickSearch');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.toLowerCase();
      document.querySelectorAll('[data-searchable]').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }
});

// Helper: percentage color class
function pctClass(pct) {
  if (pct >= 75) return 'high';
  if (pct >= 50) return 'medium';
  return 'low';
}

// Helper: set progress bar width after paint
function initProgressBars() {
  document.querySelectorAll('.att-progress-bar').forEach(bar => {
    const w = bar.dataset.width || 0;
    bar.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { bar.style.width = w + '%'; }, 50);
    });
  });
}
window.addEventListener('load', initProgressBars);
