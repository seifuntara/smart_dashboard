console.log("Analytics JS loaded");

let categoryChart = null;
let monthlyChart = null;

/* ================= CATEGORY CHART ================= */
async function loadCategoryChart() {
  const canvas = document.getElementById("categoryChart");
  if (!canvas) return;

  const res = await fetch("/analytics/category");
  const data = await res.json();

  if (!data || Object.keys(data).length === 0) {
    canvas.parentElement.innerHTML =
      "<p class='text-muted text-center'>No category data available</p>";
    return;
  }

  if (categoryChart) categoryChart.destroy();

  const labels = Object.keys(data);
  const values = Object.values(data);
  const total = values.reduce((a, b) => a + b, 0);

  categoryChart = new Chart(canvas, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [{
        data: values
      }]
    },
    options: {
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              const value = context.raw;
              const percent = ((value / total) * 100).toFixed(1);
              return `${context.label}: ${percent}%`;
            }
          }
        },
        legend: {
          position: "bottom"
        }
      }
    }
  });
}

/* ================= MONTHLY CHART ================= */
async function loadMonthlyChart() {
  const canvas = document.getElementById("monthlyChart");
  if (!canvas) return;

  const res = await fetch("/analytics/monthly");
  const data = await res.json();

  if (!data || Object.keys(data).length === 0) {
    canvas.parentElement.innerHTML =
      "<p class='text-muted text-center'>No monthly data available</p>";
    return;
  }

  if (monthlyChart) monthlyChart.destroy();

  monthlyChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: Object.keys(data),
      datasets: [{
        label: "Total Spending (SGD)",
        data: Object.values(data),
        tension: 0.3,
        pointRadius: 4,
        fill: false
      }]
    },
    options: {
      plugins: {
        legend: {
          display: true
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Amount (SGD)"
          }
        },
        x: {
          title: {
            display: true,
            text: "Month"
          }
        }
      }
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

  if (!transactions || transactions.length === 0) {
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

/* ================= WHAT-IF ANALYSIS ================= */
async function runWhatIf() {
  const category = document.getElementById("whatIfCategory").value;
  const delta = Number(document.getElementById("whatIfDelta").value);

  if (isNaN(delta)) {
    document.getElementById("whatIfResult").innerHTML =
      "<p class='text-danger'>Please enter a valid number.</p>";
    return;
  }

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

/* ================= LOAD WHEN ANALYTICS TAB OPENS ================= */
const analyticsTabBtn =
  document.querySelector('button[data-bs-target="#analytics"]');

if (analyticsTabBtn) {
  analyticsTabBtn.addEventListener("shown.bs.tab", () => {
    console.log("Analytics tab opened");
    loadCategoryChart();
    loadMonthlyChart();
    loadTransactionsTable();
  });
}
