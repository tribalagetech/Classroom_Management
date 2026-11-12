// static/js/calendar_days.js: click a day to see its details (and add an event if allowed)
(function () {
  'use strict';

  const dataEl = document.getElementById('day-data');
  const modalEl = document.getElementById('dayModal');
  if (!dataEl || !modalEl) return;

  const days = JSON.parse(dataEl.textContent);
  const el = (id) => document.getElementById(id);
  const form = el('dayForm');                      // missing for people who cannot add events
  let current = null;

  // every piece of user text goes in through textContent, so a title can never inject HTML
  function node(tag, className, text) {
    const n = document.createElement(tag);
    if (className) n.className = className;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function openDay(key) {
    const info = days[key];
    if (!info) return;
    current = key;

    el('dayTitle').textContent = info.label;

    const bits = [];
    if (info.term) bits.push(`${info.term}, week ${info.week}`);
    else if (info.status === 'break') bits.push('School holiday');
    if (info.weekend) bits.push('Weekend');
    el('dayMeta').textContent = bits.join(' · ') || 'No term set for this date';

    const list = el('dayEvents');
    list.textContent = '';
    if (!info.events.length) {
      list.appendChild(node('div', 'text-muted small', 'Nothing scheduled on this day.'));
    }
    info.events.forEach((ev) => {
      const box = node('div', 'mb-2');
      box.appendChild(node('span', `cal-chip d-inline-block me-1 ev-${ev.type}`, ev.type_label));
      box.appendChild(node('strong', '', ev.title + (ev.confirmed ? '' : '*')));
      if (ev.edit_url) {
        const edit = node('a', 'small ms-2', 'Edit');
        edit.href = ev.edit_url;
        box.appendChild(edit);
      }
      const detail = [ev.time, ev.description].filter(Boolean).join(' · ');
      if (detail) box.appendChild(node('div', 'small text-muted', detail));
      list.appendChild(box);
    });

    if (form) {                                    // reset the add form for this day
      form.reset();
      form.querySelectorAll('[data-err]').forEach((s) => { s.textContent = ''; });
      el('dayAlert').classList.add('d-none');
      el('dayEnd').min = key;                      // an end date can never be before this day
    }
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
  }

  // delegated click, so it works for every cell
  const table = document.querySelector('.cal-table');
  table.addEventListener('click', (e) => {
    const cell = e.target.closest('.cal-clickable');
    if (cell) openDay(cell.dataset.date);
  });
  table.addEventListener('keydown', (e) => {       // keyboard: Enter or Space on a focused day
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const cell = e.target.closest('.cal-clickable');
    if (cell) { e.preventDefault(); openDay(cell.dataset.date); }
  });

  modalEl.addEventListener('shown.bs.modal', () => {
    if (form) form.elements.title.focus();         // ready to type straight away
  });

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    form.querySelectorAll('[data-err]').forEach((s) => { s.textContent = ''; });
    el('dayAlert').classList.add('d-none');

    const body = new FormData(form);               // includes the CSRF token, title, type, end date, confirmed
    body.append('start_date', current);

    const btn = el('daySave');
    btn.disabled = true;
    try {
      const resp = await fetch(form.dataset.url, {
        method: 'POST', body, headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const out = await resp.json();
      if (out.ok) {
        bootstrap.Modal.getInstance(modalEl).hide();
        window.location.href = `${window.location.pathname}?day=${current}`;   // reload, keeping the day highlighted
        return;
      }
      const general = [];
      Object.entries(out.errors || {}).forEach(([field, msgs]) => {
        const slot = form.querySelector(`[data-err="${field}"]`);
        if (slot) slot.textContent = msgs.join(' '); else general.push(msgs.join(' '));
      });
      if (general.length) {
        el('dayAlert').textContent = general.join(' ');
        el('dayAlert').classList.remove('d-none');
      }
    } catch (err) {
      el('dayAlert').textContent = 'Could not save. Please check your connection and try again.';
      el('dayAlert').classList.remove('d-none');
    } finally {
      btn.disabled = false;
    }
  });
})();