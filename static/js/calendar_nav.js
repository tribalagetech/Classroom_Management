// static/js/calendar_nav.js: the "jump to month / date" pop-up
(function () {
  'use strict';

  const root = document.getElementById('calPicker');
  if (!root) return;

  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                  'August', 'September', 'October', 'November', 'December'];
  const el = (id) => document.getElementById(id);
  const pad = (n) => String(n).padStart(2, '0');
  const iso = (y, m, d) => `${y}-${pad(m + 1)}-${pad(d)}`;      // m is 0-based here

  const urlTemplate = root.dataset.url;                          // /calendar/9999/99/
  const pageYear = parseInt(root.dataset.year, 10);
  const pageMonth = parseInt(root.dataset.month, 10) - 1;        // 0-based
  const selected = root.dataset.selected;                        // '' or YYYY-MM-DD
  const today = root.dataset.today;

  let viewYear = pageYear, viewMonth = pageMonth, mode = 'days'; // 'days' or 'months'

  function go(year, month, day) {
    let url = urlTemplate.replace('9999/99', `${year}/${month + 1}`);
    if (day) url += `?day=${day}`;
    window.location.href = url;
  }

  function node(tag, className, text) {
    const n = document.createElement(tag);
    if (className) n.className = className;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function render() {
    const body = el('cpBody');
    body.innerHTML = '';

    if (mode === 'months') {
      el('cpTitle').textContent = viewYear;
      el('cpOpen').classList.add('d-none');
      const grid = node('div', 'cp-months');
      MONTHS.forEach((name, i) => {
        const b = node('button', 'cp-month', name.slice(0, 3));
        b.type = 'button';
        b.dataset.month = i;
        if (viewYear === pageYear && i === pageMonth) b.classList.add('cp-current');
        grid.appendChild(b);
      });
      body.appendChild(grid);
      return;
    }

    el('cpTitle').textContent = `${MONTHS[viewMonth]} ${viewYear}`;
    const open = el('cpOpen');
    open.classList.remove('d-none');
    open.textContent = `Open ${MONTHS[viewMonth]} ${viewYear}`;

    const head = node('div', 'cp-grid cp-head');
    ['M', 'T', 'W', 'T', 'F', 'S', 'S'].forEach((l) => head.appendChild(node('span', '', l)));
    body.appendChild(head);

    const grid = node('div', 'cp-grid');
    const lead = (new Date(viewYear, viewMonth, 1).getDay() + 6) % 7;   // blanks so Monday comes first
    for (let i = 0; i < lead; i++) grid.appendChild(node('span'));
    const count = new Date(viewYear, viewMonth + 1, 0).getDate();
    for (let d = 1; d <= count; d++) {
      const key = iso(viewYear, viewMonth, d);
      const b = node('button', 'cp-day', d);
      b.type = 'button';
      b.dataset.date = key;
      const dow = new Date(viewYear, viewMonth, d).getDay();
      if (dow === 0 || dow === 6) b.classList.add('cp-weekend');
      if (key === today) b.classList.add('cp-today');
      if (key === selected) b.classList.add('cp-selected');
      grid.appendChild(b);
    }
    body.appendChild(grid);
  }

  function step(delta) {                                         // arrows inside the pop-up
    if (mode === 'months') {
      viewYear = Math.min(2100, Math.max(2000, viewYear + delta));
    } else {
      const d = new Date(viewYear, viewMonth + delta, 1);
      if (d.getFullYear() < 2000 || d.getFullYear() > 2100) return;
      viewYear = d.getFullYear();
      viewMonth = d.getMonth();
    }
    render();
  }

  // always start from the month the page is showing
  root.addEventListener('show.bs.dropdown', () => {
    viewYear = pageYear; viewMonth = pageMonth; mode = 'days';
    render();
  });

  el('cpPrev').addEventListener('click', () => step(-1));
  el('cpNext').addEventListener('click', () => step(1));
  el('cpTitle').addEventListener('click', () => { mode = mode === 'days' ? 'months' : 'days'; render(); });
  el('cpOpen').addEventListener('click', () => go(viewYear, viewMonth));

  el('cpBody').addEventListener('click', (e) => {
    const m = e.target.closest('.cp-month');
    if (m) { viewMonth = parseInt(m.dataset.month, 10); mode = 'days'; render(); return; }
    const d = e.target.closest('.cp-day');
    if (d) go(viewYear, viewMonth, d.dataset.date);
  });

  // after jumping to a date, scroll the page to it
  if (selected) {
    const cell = document.getElementById('d-' + selected);
    if (cell) cell.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
})();