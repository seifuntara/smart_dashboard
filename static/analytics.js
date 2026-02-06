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
  const category = document.getElementById("whatIfCategory").value;
  const delta = document.getElementById("whatIfDelta").value;

  const res = await fetch("/what-if", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category, delta })
  });

  const data = await res.json();

  document.getElementById("whatIfResult").innerHTML = `
    <p><b>New total spend:</b> $${data.new_total_spend.toFixed(2)}</p>
    <p><b>New savings:</b> $${data.new_savings.toFixed(2)}</p>
  `;
}

/* ================= LOAD WHEN TAB OPENS ================= */
document
  .querySelector('button[data-bs-target="#analytics"]')
  .addEventListener("shown.bs.tab", () => {
    loadCategoryChart();
    loadMonthlyChart();
    loadTransactionsTable();
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
    }, 100);
  });
}

/* ================= TRANSACTION FORM SUBMISSION ================= */
// Transaction form submission is handled in the page (`dashboard.html`).
// Removing duplicate handler here to avoid double submissions and
// conflicting request formats (JSON vs FormData) which caused errors.
