/**
 * rates.js  –  Mandi Rates page
 */

let _allRates = [];

document.addEventListener("DOMContentLoaded", loadRates);

async function loadRates() {
  const cardsEl = document.getElementById("rateCards");
  const tbody   = document.getElementById("rateTableBody");

  try {
    const res = await fetch("/api/mandi");
    _allRates  = await res.json();
    renderRateCards(_allRates);
    renderRateTable(_allRates);
    updateSummary(_allRates);

    const el = document.getElementById("lastUpdated");
    if (el && _allRates.length) el.textContent = "Updated: " + _allRates[0].date;
  } catch {
    if (cardsEl) cardsEl.innerHTML = `<div class="col-12 text-muted">⚠️ Could not load rates.</div>`;
  }
}

function updateSummary(data) {
  const rising  = data.filter(p => p.trend.includes("↑")).length;
  const falling = data.filter(p => p.trend.includes("↓")).length;
  const stable  = data.filter(p => p.trend.includes("→")).length;
  setText("rs-rising",  rising);
  setText("rs-falling", falling);
  setText("rs-stable",  stable);
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function renderRateCards(prices) {
  const el = document.getElementById("rateCards");
  if (!el) return;
  const trendIcon  = t => t.includes("↑") ? "📈" : t.includes("↓") ? "📉" : "➡️";
  const trendClass = t => t.includes("↑") ? "text-success" : t.includes("↓") ? "text-danger" : "text-muted";

  el.innerHTML = prices.map(p => `
    <div class="col-6 col-md-4 col-lg-3 col-xl-2">
      <div class="km-rate-card text-center">
        <div class="km-rate-crop">${p.crop}</div>
        <div class="km-rate-price">₹${p.modal_price}</div>
        <div class="km-rate-unit text-muted">/Quintal</div>
        <div class="km-rate-trend ${trendClass(p.trend)}">${trendIcon(p.trend)} ${p.trend}</div>
        <div class="km-rate-mandi text-muted">${p.mandi}</div>
      </div>
    </div>`).join("");
}

function renderRateTable(prices) {
  const tbody = document.getElementById("rateTableBody");
  if (!tbody) return;
  const trendClass = t => t.includes("↑") ? "km-trend-up fw-semibold" : t.includes("↓") ? "km-trend-down fw-semibold" : "km-trend-flat text-muted";

  tbody.innerHTML = prices.map(p => `
    <tr>
      <td class="fw-bold">${p.crop}</td>
      <td class="fw-bold text-success">₹${p.modal_price}</td>
      <td class="text-muted">₹${p.min_price}</td>
      <td class="text-muted">₹${p.max_price}</td>
      <td class="${trendClass(p.trend)}">${p.trend}</td>
      <td>${p.mandi}</td>
      <td class="text-muted">${p.date}</td>
      <td>
        <a href="/chat?q=${encodeURIComponent(p.crop + ' mandi rate today?')}"
           class="btn btn-xs km-refresh-btn">Ask AI</a>
      </td>
    </tr>`).join("");
}

/* ── Filters & Sort ──────────────────────────────────────── */
function filterRates(q) {
  const ql = q.toLowerCase();
  const f  = _allRates.filter(p => p.crop.toLowerCase().includes(ql));
  renderRateCards(f);
  renderRateTable(f);
}

function sortRates(by) {
  let sorted = [..._allRates];
  if (by === "price_high") sorted.sort((a, b) => b.modal_price - a.modal_price);
  else if (by === "price_low") sorted.sort((a, b) => a.modal_price - b.modal_price);
  else if (by === "trend") sorted.sort((a, b) => a.trend.localeCompare(b.trend));
  else sorted.sort((a, b) => a.crop.localeCompare(b.crop));
  renderRateCards(sorted);
  renderRateTable(sorted);
}
