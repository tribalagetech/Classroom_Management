// static/js/resource_upload.js
(function () {
  'use strict';

  const modalEl = document.getElementById('uploadModal');
  if (!modalEl) return;                               // people who cannot upload have no pop-up

  const map = JSON.parse(document.getElementById('subject-levels').textContent);
  const form = document.getElementById('uploadForm');
  const subject = form.querySelector('[name=subject]');
  const file = form.querySelector('[name=file]');
  const note = document.getElementById('fileNote');
  const boxes = () => form.querySelectorAll('#levelBoxes input[type=checkbox]');
  const MAX = parseFloat(modalEl.dataset.maxMb) * 1024 * 1024;
  const OK = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png'];

  // only the year levels this subject covers can be ticked
  function applySubject(autoTick) {
    const allowed = map[subject.value];               // undefined when no subject is chosen
    const restricted = allowed && allowed.length > 0;
    boxes().forEach((b) => {
      const ok = !restricted || allowed.includes(parseInt(b.value, 10));
      b.disabled = !ok;                               // a disabled box is not submitted
      if (!ok) b.checked = false;
      else if (autoTick && restricted) b.checked = true;
    });
  }
  subject.addEventListener('change', () => applySubject(true));
  applySubject(false);                                // keeps your ticks when the pop-up re-opens with errors

  // catch a wrong file type or a file that is too big before uploading
  file.addEventListener('change', () => {
    note.textContent = '';
    const f = file.files[0];
    if (!f) return;
    const ext = f.name.split('.').pop().toLowerCase();
    if (!OK.includes(ext)) {
      note.textContent = `.${ext} files are not allowed.`;
      file.value = '';
    } else if (f.size > MAX) {
      note.textContent = `That file is ${(f.size / 1048576).toFixed(1)} MB. The limit is ${modalEl.dataset.maxMb} MB.`;
      file.value = '';
    }
  });

  // the server found errors: re-open the pop-up so they can be read
  if (modalEl.dataset.open === '1') bootstrap.Modal.getOrCreateInstance(modalEl).show();
})();