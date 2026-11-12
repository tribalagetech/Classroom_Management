// static/js/term_modal.js
(function () {
  'use strict';

  const modalEl = document.getElementById('termModal');
  if (!modalEl) return;                          // page without the pop-up (e.g. teachers)

  const terms = JSON.parse(document.getElementById('terms-data').textContent);
  const VIEW_YEAR = parseInt(modalEl.dataset.year, 10);   // the year shown on the calendar page
  const BREAK = { ONE: 1, TWO: 2 };
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                  'August', 'September', 'October', 'November', 'December'];

  const el = (id) => document.getElementById(id);
  const form = el('termForm');
  const f = { number: el('tmNumber'), weeks: el('tmWeeks'), start: el('tmStart'), end: el('tmEnd'),
              brk: el('tmBreak'), info: el('tmInfo'), confirmed: el('tmConfirmed') };

  /* ---------- date helpers (noon avoids daylight-saving surprises) ---------- */
  const mk = (y, m, d) => new Date(y, m, d, 12);
  const pad = (n) => String(n).padStart(2, '0');
  const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const fromISO = (s) => { const [y, m, d] = s.split('-').map(Number); return mk(y, m - 1, d); };
  const dmy = (d) => `${pad(d.getDate())}-${pad(d.getMonth() + 1)}-${d.getFullYear()}`;   // DD-MM-YYYY
  const long = (d) => d.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const addDays = (d, n) => mk(d.getFullYear(), d.getMonth(), d.getDate() + n);
  const diffDays = (a, b) => Math.round((b - a) / 86400000);              // days from a to b
  const sameDay = (a, b) => !!a && !!b && iso(a) === iso(b);
  const fridayOf = (d) => addDays(d, (5 - d.getDay() + 7) % 7);           // the Friday on or after d
  const mondayOnOrAfter = (d) => addDays(d, (1 - d.getDay() + 7) % 7);
  const weeksBetween = (a, b) => Math.round((diffDays(a, b) + 1) / 7);    // same rule as the server

  function parseDMY(text) {                                               // accepts 25-01-2027, 25/01/2027
    const m = /^(\d{1,2})[-\/.](\d{1,2})[-\/.](\d{4})$/.exec(text.trim());
    if (!m) return null;
    const d = mk(+m[3], +m[2] - 1, +m[1]);
    return (d.getMonth() === +m[2] - 1 && d.getDate() === +m[1]) ? d : null;   // rejects 31-02-2027
  }

  /* ---------- state ---------- */
  let start = null, end = null, pick = 'start', editing = null;
  let view = mk(VIEW_YEAR, 0, 1);                                         // month shown in the mini calendar

  const findTerm = (year, number) => terms.find((t) => t.year === year && t.number === number);
  const termYear = () => (start ? start.getFullYear() : VIEW_YEAR);

  /* ---------- keeping the fields in step ---------- */
  function syncEndFromWeeks() {                    // weeks typed -> end = Friday of the last week
    const w = parseInt(f.weeks.value, 10);
    if (start && w >= 1 && w <= 20) end = fridayOf(addDays(start, (w - 1) * 7));
  }
  function syncWeeksFromEnd() {                    // end changed -> weeks follow
    if (start && end && end >= start) f.weeks.value = weeksBetween(start, end);
  }
  const writeEnd = () => { if (end) f.end.value = dmy(end); };
  function writeInputs() {
    f.start.value = start ? dmy(start) : '';
    f.end.value = end ? dmy(end) : '';
  }

  /* ---------- helper notes under the fields ---------- */
  function refreshBreakNote() {
    const note = el('tmBreakNote');
    note.textContent = '';
    const v = f.brk.value;
    if (!v || !end) return;
    if (BREAK[v]) {
      const next = mondayOnOrAfter(addDays(end, BREAK[v] * 7));
      note.textContent = `The next term would start on ${long(next)}.`;
    } else if (v === 'XMAS') {
      const t1 = findTerm(termYear(), 1);
      if (!t1) { note.textContent = 'Add Term 1 first, so the Christmas holiday can be calculated.'; return; }
      const nextT1 = addDays(fromISO(t1.start), 364);   // same weekday, one year later
      const weeks = Math.round(diffDays(addDays(end, 1), nextT1) / 7);
      note.textContent = `About ${weeks} weeks, until ${long(nextT1)} (estimated from this year's Term 1 start).`;
    }
  }

  function refresh() {
    el('tmStartName').textContent = start ? long(start) : '';
    el('tmEndName').textContent = end ? long(end) : '';
    el('tmSummary').textContent = (start && end && end >= start)
      ? `Runs ${dmy(start)} to ${dmy(end)}: ${weeksBetween(start, end)} weeks.`
      : 'Enter a start date and the number of weeks (or an end date).';
    const n = parseInt(f.number.value, 10);
    el('tmExisting').textContent = (n && findTerm(termYear(), n))
      ? `Term ${n} ${termYear()} is already set. Saving will update it.` : '';
    refreshBreakNote();
    renderMini();
  }

  /* ---------- helper calendar ---------- */
  function renderMini() {
    const y = view.getFullYear(), m = view.getMonth();
    el('mcTitle').textContent = `${MONTHS[m]} ${y}`;
    const grid = el('mcGrid');
    grid.innerHTML = '';
    const lead = (mk(y, m, 1).getDay() + 6) % 7;                 // blank cells so Monday comes first
    for (let i = 0; i < lead; i++) grid.appendChild(document.createElement('span'));
    const selected = parseInt(f.number.value, 10);
    for (let day = 1; day <= new Date(y, m + 1, 0).getDate(); day++) {
      const date = mk(y, m, day);
      const key = iso(date);
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'mc-day';
      b.textContent = day;
      b.dataset.date = key;
      if (date.getDay() === 0 || date.getDay() === 6) b.classList.add('mc-weekend');
      if (terms.some((t) => !(t.year === termYear() && t.number === selected) && key >= t.start && key <= t.end))
        b.classList.add('mc-other');
      if (start && end && date >= start && date <= end) b.classList.add('mc-range');
      if (sameDay(date, start)) b.classList.add('mc-start');
      if (sameDay(date, end)) b.classList.add('mc-end');
      grid.appendChild(b);
    }
  }

  function setPick(mode) {
    pick = mode;
    document.querySelectorAll('[data-pick]').forEach((b) => b.classList.toggle('active', b.dataset.pick === mode));
  }

  /* ---------- loading, resetting and choosing a term ---------- */
  function clearFields() {
    start = end = null; editing = null;
    f.weeks.value = ''; f.brk.value = ''; f.info.value = ''; f.confirmed.checked = true;
  }

  function loadTerm(t) {                          // fill the pop-up from a saved term (edit mode)
    editing = { year: t.year, number: t.number };
    f.number.value = String(t.number);
    start = fromISO(t.start);
    end = fromISO(t.end);
    f.weeks.value = weeksBetween(start, end);
    f.brk.value = t.break_after || '';
    f.info.value = t.staff_info || '';
    f.confirmed.checked = t.confirmed;
    view = mk(start.getFullYear(), start.getMonth(), 1);
    setPick('start');
    writeInputs();
    refresh();
  }

  function onTermChange() {
    const n = parseInt(f.number.value, 10);
    if (!n) { refresh(); return; }
    const existing = findTerm(VIEW_YEAR, n);
    if (existing) { loadTerm(existing); return; }   // picking a saved term opens it for editing
    if (editing) clearFields();                     // leaving an edit: start from a clean form

    // suggest a start date: the previous term's end + its chosen holiday
    const prev = findTerm(VIEW_YEAR, n - 1);
    if (!start && prev && BREAK[prev.break_after]) {
      start = mondayOnOrAfter(addDays(fromISO(prev.end), BREAK[prev.break_after] * 7));
      if (!f.weeks.value) f.weeks.value = 10;       // a typical term length, change it if needed
      syncEndFromWeeks();
      view = mk(start.getFullYear(), start.getMonth(), 1);
      setPick('end');
    }
    writeInputs();
    refresh();
  }

  function resetForm() {
    clearFields();
    clearErrors();
    const free = [1, 2, 3, 4].find((n) => !findTerm(VIEW_YEAR, n));   // first term not set yet
    f.number.value = free ? String(free) : '';
    view = mk(VIEW_YEAR, 0, 1);
    setPick('start');
    onTermChange();
  }

  /* ---------- errors ---------- */
  function clearErrors() {
    el('termAlert').classList.add('d-none');
    form.querySelectorAll('[data-err]').forEach((s) => { s.textContent = ''; });
  }
  function showErrors(errors) {
    const general = [];
    Object.entries(errors).forEach(([field, msgs]) => {
      const slot = form.querySelector(`[data-err="${field}"]`);
      if (slot) slot.textContent = msgs.join(' '); else general.push(msgs.join(' '));
    });
    if (general.length) {
      const box = el('termAlert');
      box.textContent = general.join(' ');
      box.classList.remove('d-none');
    }
  }

  /* ---------- events ---------- */
  modalEl.addEventListener('show.bs.modal', (e) => {          // runs each time the pop-up opens
    const t = e.relatedTarget;                                // the button that opened it
    if (t && t.dataset.termNumber) {
      const found = findTerm(parseInt(t.dataset.termYear, 10), parseInt(t.dataset.termNumber, 10));
      if (found) { clearErrors(); loadTerm(found); return; }
    }
    resetForm();
  });

  f.number.addEventListener('change', onTermChange);
  f.brk.addEventListener('change', refresh);

  f.weeks.addEventListener('input', () => { syncEndFromWeeks(); writeEnd(); refresh(); });

  f.start.addEventListener('input', () => {                   // typed: do not rewrite the box under the cursor
    start = parseDMY(f.start.value);
    if (start) {
      view = mk(start.getFullYear(), start.getMonth(), 1);
      if (f.weeks.value) { syncEndFromWeeks(); writeEnd(); }
    }
    refresh();
  });
  f.end.addEventListener('input', () => {
    end = parseDMY(f.end.value);
    syncWeeksFromEnd();
    refresh();
  });

  // the small calendar buttons next to the date boxes open the browser's date picker
  document.querySelectorAll('.date-field').forEach((box) => {
    const text = box.querySelector('input[type=text]');
    const native = box.querySelector('input[type=date]');
    box.querySelector('button').addEventListener('click', () => {
      if (native.showPicker) native.showPicker(); else native.focus();
    });
    native.addEventListener('change', () => {
      if (!native.value) return;
      text.value = dmy(fromISO(native.value));
      text.dispatchEvent(new Event('input'));
    });
  });

  // helper calendar: click a day to set the start or the end
  el('mcGrid').addEventListener('click', (e) => {
    const b = e.target.closest('.mc-day');
    if (!b) return;
    const d = fromISO(b.dataset.date);
    if (pick === 'start') {
      start = d;
      if (f.weeks.value) syncEndFromWeeks(); else end = null;
      setPick('end');                                          // next click adjusts the end
    } else {
      if (start && d < start) return;                          // an end before the start makes no sense
      end = d;
      syncWeeksFromEnd();
    }
    writeInputs();
    refresh();
  });
  el('mcPrev').addEventListener('click', () => { view = mk(view.getFullYear(), view.getMonth() - 1, 1); renderMini(); });
  el('mcNext').addEventListener('click', () => { view = mk(view.getFullYear(), view.getMonth() + 1, 1); renderMini(); });
  document.querySelectorAll('[data-pick]').forEach((b) => b.addEventListener('click', () => setPick(b.dataset.pick)));

  /* ---------- save without leaving the page ---------- */
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();
    if (!start || !end) {
      showErrors({ __all__: ['Enter a valid start date and end date in DD-MM-YYYY format.'] });
      return;
    }
    const body = new FormData();
    body.append('csrfmiddlewaretoken', form.querySelector('[name=csrfmiddlewaretoken]').value);
    body.append('number', f.number.value);
    body.append('weeks', f.weeks.value);
    body.append('start_date', iso(start));                    // the server wants YYYY-MM-DD
    body.append('end_date', iso(end));
    body.append('break_after', f.brk.value);
    body.append('staff_info', f.info.value);
    if (f.confirmed.checked) body.append('confirmed', 'on');

    const saveBtn = el('tmSave');
    saveBtn.disabled = true;
    try {
      const resp = await fetch(form.dataset.url, {
        method: 'POST', body, headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const out = await resp.json();
      if (out.ok) {
        bootstrap.Modal.getInstance(modalEl).hide();
        window.location.reload();                            // same page: the green message and new data appear
      } else {
        showErrors(out.errors || {});
      }
    } catch (err) {
      showErrors({ __all__: ['Could not save. Please check your connection and try again.'] });
    } finally {
      saveBtn.disabled = false;
    }
  });
})();