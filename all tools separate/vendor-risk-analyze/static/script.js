/* ═══════════════════════════════════════
   VendorGuard Dashboard — script.js
   ═══════════════════════════════════════ */

/* ══ State ══ */
const state = {
  allData: [],       // full dataset from data.json
  filtered: [],       // after filters applied
  currentPage: 1,
  pageSize: 25,       // rows per page (or 'all')
  riskFilter: 'all',
  typeFilter: 'all',
  buFilter: 'all',
  statusFilter: 'all',
  search: ''
};

/* ══ Risk & Status config ══ */
const RISK_CONFIG = {
  critical: { label: 'Critical', dot: '#dc2626', cls: 'rb-critical' },
  high: { label: 'High', dot: '#ea580c', cls: 'rb-high' },
  medium: { label: 'Medium', dot: '#d97706', cls: 'rb-medium' },
  low: { label: 'Low', dot: '#16a34a', cls: 'rb-low' }
};

const STATUS_CONFIG = {
  Accepted: { cls: 'st-accepted', icon: '✅' },
  Rejected: { cls: 'st-rejected', icon: '❌' },
  Pending: { cls: 'st-pending', icon: '⏳' }
};

const BUS = ['All', 'HR', 'Sales', 'Marketing', 'Legal', 'Engineering', 'Finance', 'Data', 'Product', 'Operations', 'Security', 'IT Security'];

/* ════════════════════════════════════════
   INIT — fetch data.json and bootstrap
   ════════════════════════════════════════ */
function loadDashboard() {
  fetch('/api/dashboard')
    .then(res => res.json())
    .then(data => {

      state.allData = data.map(d => ({
        ...d,

        // normalize values
        risk_level: (d.risk_level || '').toLowerCase(),
        status: d.status,

        submittedAt: d.timestamp || '',

        vendor_id: d.vendor_id || '',
        vendor_domain: d.vendor_domain || '',
        resource_type: d.resource_type || '',
        business_unit: d.business_unit || ''
      }));

      buildSidebar();
      buildBUPills();
      applyFilters();
    })
    .catch(err => {
      console.error("Dashboard load failed:", err);

      // show error in UI
      document.getElementById('tableBody').innerHTML =
        `<tr class="empty-row">
          <td colspan="9">
            <div class="empty-icon">⚠️</div>
            <div>Failed to load dashboard<br><small>${err.message}</small></div>
          </td>
        </tr>`;
    });
}


function goToOldDashboard() {
  window.location.href = "/old";
}

/* ════════════════════════════════════════
   BUILD SIDEBAR FILTERS
   ════════════════════════════════════════ */
function buildSidebar() {
  // ── Risk filters ──
  const rf = document.getElementById('riskFilters');
  const riskOrder = ['all', 'critical', 'high', 'medium', 'low'];
  riskOrder.forEach(r => {
    const count = r === 'all'
      ? state.allData.length
      : state.allData.filter(d => d.risk_level === r).length;
    const cfg = RISK_CONFIG[r];
    const btn = document.createElement('button');
    btn.className = 'filter-item' + (r === 'all' ? ' active' : '');
    btn.id = 'rf-' + r;
    btn.innerHTML = `
      <div class="fi-dot" style="background:${cfg ? cfg.dot : '#8b92aa'}"></div>
      ${cfg ? cfg.label : 'All Risks'}
      <span class="fi-count">${count}</span>`;
    btn.onclick = () => setRisk(r);
    rf.appendChild(btn);
  });

  // ── Type filters ──
  const tf = document.getElementById('typeFilters');
  const types = ['all', ...new Set(state.allData.map(d => d.resource_type).filter(Boolean).sort())];
  types.forEach(t => {
    const count = t === 'all' ? state.allData.length : state.allData.filter(d => d.resource_type === t).length;
    const btn = document.createElement('button');
    btn.className = 'filter-item' + (t === 'all' ? ' active' : '');
    btn.id = 'tf-' + t;
    btn.innerHTML = `
      <div class="fi-dot" style="background:#2563eb"></div>
      ${t === 'all' ? 'All Types' : t}
      <span class="fi-count">${count}</span>`;
    btn.onclick = () => setType(t);
    tf.appendChild(btn);
  });

  // ── BU filters (sidebar) ──
  const bf = document.getElementById('buFilters');
  const bus = ['all', ...new Set(state.allData.map(d => d.business_unit).filter(Boolean).sort())];
  bus.forEach(b => {
    const count = b === 'all' ? state.allData.length : state.allData.filter(d => d.business_unit === b).length;
    const btn = document.createElement('button');
    btn.className = 'filter-item' + (b === 'all' ? ' active' : '');
    btn.id = 'bf-' + b;
    btn.innerHTML = `
      <div class="fi-dot" style="background:#8b92aa"></div>
      ${b === 'all' ? 'All Units' : b}
      <span class="fi-count">${count}</span>`;
    btn.onclick = () => setBU(b);
    bf.appendChild(btn);
  });
}

/* ════════════════════════════════════════
   BUILD TOP BU PILLS
   ════════════════════════════════════════ */
function buildBUPills() {
  const bp = document.getElementById('buPills');
  const bus = ['All', ...new Set(state.allData.map(d => d.business_unit).filter(Boolean).sort())];
  bus.forEach(b => {
    const pill = document.createElement('button');
    pill.className = 'bu-pill' + (b === 'All' ? ' active' : '');
    pill.id = 'bup-' + b;
    pill.textContent = b;
    pill.onclick = () => setBU(b === 'All' ? 'all' : b);
    bp.appendChild(pill);
  });
}

/* ════════════════════════════════════════
   FILTER SETTERS
   ════════════════════════════════════════ */
function setRisk(v) {
  state.riskFilter = v;
  state.currentPage = 1;
  // Update sidebar active
  document.querySelectorAll('#riskFilters .filter-item').forEach(b => b.classList.remove('active'));
  document.getElementById('rf-' + v)?.classList.add('active');
  // Update summary cards
  document.querySelectorAll('.summary-card[data-filter]').forEach(c => c.classList.remove('active-filter'));
  if (v !== 'all') document.querySelector(`.summary-card[data-filter="${v}"]`)?.classList.add('active-filter');
  applyFilters();
}

function setType(v) {
  state.typeFilter = v;
  state.currentPage = 1;
  document.querySelectorAll('#typeFilters .filter-item').forEach(b => b.classList.remove('active'));
  document.getElementById('tf-' + v)?.classList.add('active');
  applyFilters();
}

function setBU(v) {
  state.buFilter = v;
  state.currentPage = 1;
  // Update sidebar
  document.querySelectorAll('#buFilters .filter-item').forEach(b => b.classList.remove('active'));
  document.getElementById('bf-' + v)?.classList.add('active');
  // Update pills
  document.querySelectorAll('.bu-pill').forEach(p => p.classList.remove('active'));
  const pillId = v === 'all' ? 'bup-All' : 'bup-' + v;
  document.getElementById(pillId)?.classList.add('active');
  applyFilters();
}

function setStatus(v) {
  state.statusFilter = v;
  state.currentPage = 1;
  document.querySelectorAll('.summary-card[data-filter]').forEach(c => c.classList.remove('active-filter'));
  document.querySelector(`.summary-card[data-filter="${v}"]`)?.classList.add('active-filter');
  applyFilters();
}

function filterByRisk(v) {
  if (state.riskFilter === v) { setRisk('all'); } else { setRisk(v); }
}

function filterByStatus(v) {
  if (state.statusFilter === v) {
    state.statusFilter = 'all';
    document.querySelectorAll('.summary-card[data-filter]').forEach(c => c.classList.remove('active-filter'));
    state.currentPage = 1;
    applyFilters();
  } else {
    state.statusFilter = 'all'; // reset risk when switching to status
    state.riskFilter = 'all';
    document.querySelectorAll('#riskFilters .filter-item').forEach(b => b.classList.remove('active'));
    document.getElementById('rf-all')?.classList.add('active');
    setStatus(v);
  }
}

function changePageSize() {
  const sel = document.getElementById('pageSizeSelect').value;
  state.pageSize = sel === 'all' ? 'all' : parseInt(sel);
  state.currentPage = 1;
  renderTable();
  renderPagination();
}

function resetFilters() {
  state.riskFilter = 'all';
  state.typeFilter = 'all';
  state.buFilter = 'all';
  state.statusFilter = 'all';
  state.search = '';
  state.currentPage = 1;
  document.getElementById('searchInput').value = '';
  document.querySelectorAll('.filter-item').forEach(b => b.classList.remove('active'));
  document.getElementById('rf-all')?.classList.add('active');
  document.getElementById('tf-all')?.classList.add('active');
  document.getElementById('bf-all')?.classList.add('active');
  document.querySelectorAll('.summary-card').forEach(c => c.classList.remove('active-filter'));
  document.querySelectorAll('.bu-pill').forEach(p => p.classList.remove('active'));
  document.getElementById('bup-All')?.classList.add('active');
  applyFilters();
}

/* ════════════════════════════════════════
   APPLY FILTERS — core function
   ════════════════════════════════════════ */
function applyFilters() {
  state.search = document.getElementById('searchInput').value.toLowerCase().trim();

  state.filtered = state.allData.filter(row => {
    if (state.riskFilter !== 'all' && row.risk_level !== state.riskFilter) return false;
    if (state.typeFilter !== 'all' && row.resource_type !== state.typeFilter) return false;
    if (state.buFilter !== 'all' && row.business_unit !== state.buFilter) return false;
    if (state.statusFilter !== 'all' && row.status !== state.statusFilter) return false;

    if (state.search) {
      const q = state.search;
      const haystack = [
        row.vendor,
        row.vendor_id,
        row.alertTitle,
        row.alertDescription || '',
        row.resource_type,
        row.business_unit
      ].join(' ').toLowerCase();

      if (!haystack.includes(q)) return false;
    }

    return true;
  });

  updateSummaryCounts();
  renderTable(state.filtered);   // ✅ FIXED
  renderPagination();
}
/* ════════════════════════════════════════
   UPDATE SUMMARY COUNTS
   ════════════════════════════════════════ */
function updateSummaryCounts() {
  const all = state.allData;
  const totalCountEl = document.getElementById('totalCount');
  if (totalCountEl) totalCountEl.textContent = all.length;
  document.getElementById('cnt-critical').textContent = all.filter(r => r.risk_level === 'critical').length;
  document.getElementById('cnt-high').textContent = all.filter(r => r.risk_level === 'high').length;
  document.getElementById('cnt-medium').textContent = all.filter(r => r.risk_level === 'medium').length;
  document.getElementById('cnt-low').textContent = all.filter(r => r.risk_level === 'low').length;
  document.getElementById('cnt-accepted').textContent = all.filter(r => r.status === 'Accepted').length;
  document.getElementById('cnt-rejected').textContent = all.filter(r => r.status === 'Rejected').length;
  document.getElementById('cnt-pending').textContent = all.filter(r => r.status === 'Pending').length;
  document.getElementById('resultCount').textContent = state.filtered.length;
}

/* ════════════════════════════════════════
   RENDER TABLE
   ════════════════════════════════════════ */
function renderTable(data) {
  const tableBody = document.getElementById('tableBody');

  if (!tableBody) {
    console.error("tableBody not found");
    return;
  }

  if (!data.length) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align:center;padding:20px;">
          No data available
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = data.map((row, index) => {
    const statusLabel = row.status;
    return `
      <tr onclick="openDetails('${row.id}')" style="cursor:pointer;">
        <td>${index + 1}</td>
        <td>${row.vendor_id}</td>
        <td>${row.vendor}</td>
        <td>${row.alertTitle}</td>
        <td>${row.risk_level}</td>
        <td>${row.resource_type}</td>
        <td>${row.business_unit}</td>
        <td>${row.timestamp || ''}</td>
        <td>${statusLabel}</td>
        <td>
${row.jira_link
        ? `<a href="${row.jira_link}" target="_blank" onclick="event.stopPropagation()" style="color:#2563eb;font-weight:600;">🔗 View</a>`
        : '-'}
        </td>
      </tr>
    `;
  }).join('');
}

function openDetails(id) {
  window.location.href = `/details?id=${id}`;
}

/* ════════════════════════════════════════
   RENDER PAGINATION
   ════════════════════════════════════════ */
function renderPagination() {
  const bar = document.getElementById('paginationBar');
  if (state.pageSize === 'all' || state.filtered.length === 0) {
    bar.innerHTML = '';
    return;
  }

  const totalPages = Math.ceil(state.filtered.length / state.pageSize);
  if (totalPages <= 1) { bar.innerHTML = ''; return; }

  const cur = state.currentPage;
  let html = '';

  // Prev
  html += `<button class="pg-btn" onclick="goPage(${cur - 1})" ${cur === 1 ? 'disabled' : ''}>‹</button>`;

  // Page numbers with ellipsis
  const pages = getPagesArray(cur, totalPages);
  pages.forEach(p => {
    if (p === '...') {
      html += `<span class="pg-ellipsis">…</span>`;
    } else {
      html += `<button class="pg-btn ${p === cur ? 'active' : ''}" onclick="goPage(${p})">${p}</button>`;
    }
  });

  // Next
  html += `<button class="pg-btn" onclick="goPage(${cur + 1})" ${cur === totalPages ? 'disabled' : ''}>›</button>`;

  bar.innerHTML = html;
}

function getPagesArray(cur, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  if (cur <= 4) return [1, 2, 3, 4, 5, '...', total];
  if (cur >= total - 3) return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
  return [1, '...', cur - 1, cur, cur + 1, '...', total];
}

function goPage(p) {
  const totalPages = Math.ceil(state.filtered.length / state.pageSize);
  if (p < 1 || p > totalPages) return;
  state.currentPage = p;
  renderTable(state.filtered);
  renderPagination();
  document.querySelector('.table-scroll').scrollTop = 0;
}

/* ════════════════════════════════════════
   MODAL — click row to see detail
   ════════════════════════════════════════ */
function openModal(idx) {
  const row = state.allData[idx];
  if (!row) return;

  const riskCfg = RISK_CONFIG[row.risk_level] || {};
  const statusCfg = STATUS_CONFIG[row.status] || { cls: 'st-pending', icon: '⏳' };

  document.getElementById('m-vendor-id').textContent = `${row.vendor_id}  ·  ${row.vendor_domain || ''}`;
  document.getElementById('m-title').textContent = row.alertTitle;
  document.getElementById('m-risk').innerHTML = `<span class="risk-badge ${riskCfg.cls}">${(row.risk_level || '').toUpperCase()}</span>`;
  document.getElementById('m-status').innerHTML = `<span class="status-chip ${statusCfg.cls}">${statusCfg.icon} ${row.status}</span>`;
  document.getElementById('m-type').textContent = row.resource_type || '—';
  document.getElementById('m-bu').textContent = row.business_unit || '—';
  document.getElementById('m-domain').textContent = row.vendor_domain || '—';
  document.getElementById('m-alert-id').textContent = row.alert_id || '—';
  document.getElementById('m-date').textContent = (row.submittedAt || '—').substring(0, 19).replace('T', ' ');
  document.getElementById('m-desc').textContent = row.alertDescription || '—';

  const actionWrap = document.getElementById('m-action-wrap');
  const actionEl = document.getElementById('m-action');
  if (row.action_item) {
    actionWrap.style.display = 'block';
    actionEl.textContent = row.action_item;
  } else {
    actionWrap.style.display = 'none';
  }

  document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

// Close modal on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

document.addEventListener('DOMContentLoaded', function () {
  loadDashboard();

  // 🔁 auto refresh every 5 seconds
  setInterval(loadDashboard, 5000);
});

/* ════════════════════════════════════════
   UTILITY — escape HTML
   ════════════════════════════════════════ */
function esc(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
// button 
function generateAlert() {
  console.log("Generating new alert...");

  fetch('/api/generate-alert', {
    method: 'POST'
  })
    .then(res => res.json())
    .then(data => {
      console.log("New alert created:", data);

      // 🔥 Reload dashboard
      loadDashboard();

      // 🔥 Optional toast
      alert("New alert generated successfully!");
    })
    .catch(err => {
      console.error("Generate alert failed:", err);
      alert("Failed to generate alert");
    });
}