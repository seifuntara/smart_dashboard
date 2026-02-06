console.log("Analytics JS loaded");

let categoryChart = null;
let monthlyChart = null;

/* ================= CATEGORY CHART ================= */
async function loadCategoryChart() {
  const canvas = document.getElementById("categoryChart");
  if (!canvas) return;

  const res = await fetch("/analytics/category");
  const data = await res.json();

  if (Object.keys(data).length === 0) return;

  if (categoryChart) categoryChart.destroy();

  categoryChart = new Chart(canvas, {
    type: "pie",
    data: {
      labels: Object.keys(data),
      datasets: [{
        data: Object.values(data)
      }]
    }
  });
}

/* ================= MONTHLY CHART ================= */
async function loadMonthlyChart() {
  const canvas = document.getElementById("monthlyChart");
  if (!canvas) return;

  const res = await fetch("/analytics/monthly");
  const data = await res.json();

  if (Object.keys(data).length === 0) return;

  if (monthlyChart) monthlyChart.destroy();

  monthlyChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: Object.keys(data),
      datasets: [{
        data: Object.values(data),
        tension: 0.3
      }]
    }
  });
}

/* ================= TRANSACTION TABLE ================= */
async function loadTransactionsTable() {
  const res = await fetch("/analytics/transactions");
  const transactions = await res.json();

  const tbody = document.getElementById("transactionsTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";

  if (transactions.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" class="text-center text-muted">
          No transactions yet
        </td>
      </tr>
    `;
    return;
  }

  transactions
    .sort((a, b) => new Date(b.date) - new Date(a.date))
    .forEach(txn => {
      tbody.innerHTML += `
        <tr>
          <td>${txn.date}</td>
          <td>${txn.category}</td>
          <td>${txn.merchant || "-"}</td>
          <td class="text-end">${txn.amount.toFixed(2)}</td>
        </tr>
      `;
    });
}

/* ================= WHAT IF ================= */
async function runWhatIf() {
  try {
  const rows = document.querySelectorAll('.whatif-row');
  if (!rows || rows.length === 0) {
    document.getElementById("whatIfResult").innerText = "Add at least one expense row.";
    return;
  }

  const changes = {};
  rows.forEach(row => {
    const sel = row.querySelector('select');
    const inp = row.querySelector('input[type="number"]');
    if (!sel) return;
    const cat = sel.value;
    const val = inp ? parseFloat(inp.value || 0) : 0;
    if (cat) changes[cat] = (changes[cat] || 0) + val;
  });

  const res = await fetch("/what-if", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ changes })
  });

  const data = await res.json();

  const container = document.getElementById("whatIfResult");
  if (data.error) {
    container.innerText = data.error;
    return;
  }

  let html = `
    <p><b>Original total spend:</b> $${data.original_total_spend.toFixed(2)}</p>
    <p><b>New total spend:</b> $${data.new_total_spend.toFixed(2)}</p>
    <p><b>Original savings:</b> $${data.original_savings.toFixed(2)}</p>
    <p><b>New savings:</b> $${data.new_savings.toFixed(2)}</p>
    <p><b>Savings goal:</b> $${(data.savings_goal || 0).toFixed(2)}</p>
    <p><b>Original deviation from goal:</b> ${data.original_deviation >= 0 ? '+' : ''}$${data.original_deviation.toFixed(2)}</p>
    <p><b>New deviation from goal:</b> ${data.new_deviation >= 0 ? '+' : ''}$${data.new_deviation.toFixed(2)}</p>
    <p><b>Meets goal after change:</b> ${data.meets_goal ? 'Yes' : 'No'}</p>
    <h6>Breakdown</h6>
    <ul>
  `;

  Object.keys(data.breakdown || {}).forEach(cat => {
    const b = data.breakdown[cat];
    html += `<li><b>${cat}:</b> current $${b.current.toFixed(2)}, simulated $${b.simulated.toFixed(2)} (delta ${b.delta >= 0 ? '+' : ''}${b.delta.toFixed(2)})</li>`;
  });

  html += `</ul>`;
  container.innerHTML = html;
  // store latest what-if result globally so the chat assistant can access it
  try {
    window.currentWhatIf = data;
  } catch (e) {
    console.warn('Could not set global what-if context', e);
  }
  } catch (err) {
    console.error('runWhatIf caught', err);
    const container = document.getElementById('whatIfResult');
    if (container) container.innerText = 'Error running simulation: ' + (err.message || err);
  }
}


/* ============== WHAT-IF HELPERS ============== */
let availableCategories = [];
const DEFAULT_CATEGORIES = ['Dining','Shopping','Rent','Transport','Other'];

async function loadAvailableCategories() {
  const res = await fetch('/analytics/category');
  const data = await res.json();
  const userCats = Object.keys(data || {});

  // Always include default categories first, then any user categories not already present
  availableCategories = DEFAULT_CATEGORIES.slice();
  userCats.forEach(c => {
    if (!availableCategories.includes(c)) availableCategories.push(c);
  });
}

function createCategorySelect(id, selectedValue) {
  const sel = document.createElement('select');
  sel.className = 'form-control';
  sel.id = id;
  availableCategories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat;
    opt.innerText = cat;
    if (cat === selectedValue) opt.selected = true;
    sel.appendChild(opt);
  });
  return sel;
}

function addWhatIfRow(prefillCategory = null, prefillDelta = 0) {
  const container = document.getElementById('whatIfRowsContainer');
  if (!container) return;

  const idx = Date.now();
  const row = document.createElement('div');
  row.className = 'd-flex align-items-center mb-2 whatif-row';
  row.dataset.idx = idx;

  const selWrapper = document.createElement('div');
  selWrapper.style.flex = '1';
  const sel = createCategorySelect(`whatif_cat_${idx}`, prefillCategory || availableCategories[0]);
  selWrapper.appendChild(sel);

  const inputWrapper = document.createElement('div');
  inputWrapper.style.width = '160px';
  inputWrapper.className = 'ms-2';
  const inp = document.createElement('input');
  inp.type = 'number';
  inp.step = '0.01';
  inp.className = 'form-control';
  inp.id = `whatif_delta_${idx}`;
  inp.placeholder = 'Change amount (e.g. -50)';
  inp.value = prefillDelta;
  inputWrapper.appendChild(inp);

  const btnWrapper = document.createElement('div');
  btnWrapper.className = 'ms-2';
  const rem = document.createElement('button');
  rem.type = 'button';
  rem.className = 'btn btn-outline-danger btn-sm';
  rem.innerText = 'Remove';
  rem.addEventListener('click', () => row.remove());
  btnWrapper.appendChild(rem);

  row.appendChild(selWrapper);
  row.appendChild(inputWrapper);
  row.appendChild(btnWrapper);

  container.appendChild(row);
}

function clearWhatIfRows() {
  const container = document.getElementById('whatIfRowsContainer');
  if (!container) return;
  container.innerHTML = '';
}

async function initWhatIfUI() {
  await loadAvailableCategories();
  clearWhatIfRows();
  // add one initial row
  addWhatIfRow();

  const addBtn = document.getElementById('addWhatIfBtn');
  if (addBtn) {
    addBtn.onclick = (e) => {
      e.preventDefault();
      addWhatIfRow();
    };
  }

  const runBtn = document.getElementById('runWhatIfBtn');
  if (runBtn) {
    runBtn.onclick = (e) => {
      e.preventDefault();
      // call the existing runWhatIf function
      try { runWhatIf(); } catch (err) { console.error('runWhatIf error', err); }
    };
  }
}

/* ================= LOAD WHEN TAB OPENS ================= */
document
  .querySelector('button[data-bs-target="#analytics"]')
  .addEventListener("shown.bs.tab", () => {
    loadCategoryChart();
    loadMonthlyChart();
    loadTransactionsTable();
    initWhatIfUI();
  });


const analyticsTabBtn =
  document.querySelector('button[data-bs-target="#analytics"]');

if (analyticsTabBtn) {
  analyticsTabBtn.addEventListener("shown.bs.tab", () => {
    console.log("Analytics tab opened");

    setTimeout(() => {
      loadCategoryChart();
      loadMonthlyChart();
      loadTransactionsTable();
      initWhatIfUI();
    }, 100);
  });
}

/* ================= TRANSACTION FORM SUBMISSION ================= */
// Transaction form submission is handled in the page (`dashboard.html`).
// Removing duplicate handler here to avoid double submissions and
// conflicting request formats (JSON vs FormData) which caused errors.
