// DataTables defaults
$(document).ready(function () {
  if ($.fn.DataTable) {
    $('.datatable').DataTable({
      language: {
        url: 'https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json'
      },
      pageLength: 25,
      responsive: true,
    });
  }

  // Auto-dismiss alerts after 4s
  setTimeout(() => {
    document.querySelectorAll('.alert.fade.show').forEach(el => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    });
  }, 4000);
});

// Compute abnormal flag on result input
function checkAbnormal(input, min, max) {
  const val = parseFloat(input.value);
  const row = input.closest('.result-row');
  const flagEl = row ? row.querySelector('.abnormal-badge') : null;

  row?.classList.remove('abnormal-H', 'abnormal-L', 'abnormal-C');
  if (flagEl) flagEl.textContent = '';

  if (isNaN(val) || (min === '' && max === '')) return;

  let flag = '';
  if (max !== '' && val > parseFloat(max)) flag = 'H';
  else if (min !== '' && val < parseFloat(min)) flag = 'L';

  if (flag && row) {
    row.classList.add('abnormal-' + flag);
    if (flagEl) {
      flagEl.textContent = flag;
      flagEl.className = 'abnormal-badge flag-' + flag;
    }
  }
}

// Confirm delete
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

// Print report
function printReport() { window.print(); }
