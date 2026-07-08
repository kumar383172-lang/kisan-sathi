/**
 * dashboard.js  –  Dashboard page
 */

document.addEventListener("DOMContentLoaded", () => {
  detectLocation(() => {
    loadWeatherDash();
    updateLocationBadge();
  });
  loadMandi();
  loadCrops();
});

function refreshAll() {
  loadWeatherDash();
  loadMandi();
}

function updateLocationBadge() {
  const el = document.getElementById("locationBadge");
  if (!el) return;
  const lat = window.userLat.toFixed(2);
  const lon = window.userLon.toFixed(2);
  el.innerHTML = `<i class="bi bi-geo-alt-fill me-1"></i>${lat}°N, ${lon}°E`;
}

/* ── Weather ─────────────────────────────────────────────── */
async function loadWeatherDash() {
  const body = document.getElementById("weatherBodyDash");
  if (body) body.innerHTML = `<div class="km-skeleton-block"></div><div class="km-skeleton-block short mt-2"></div>`;

  try {
    const res  = await fetch(`/api/weather?lat=${window.userLat}&lon=${window.userLon}`);
    const data = await res.json();
    renderWeatherBody(data, "weatherBodyDash");
    renderForecastRow(data.forecast || [], "forecastRow");

    // Update stat cards
    setText("sv-temp", data.temperature !== "--" ? data.temperature + "°C" : "--");
    setText("sv-hum",  data.humidity    !== "--" ? data.humidity    + "%"  : "--");
    setText("sv-soil", data.soil_moisture !== "--" ? data.soil_moisture + "%" : "--");
    setText("sv-rain", (data.precipitation || 0) + " mm");
  } catch {
    if (body) body.innerHTML = `<p class="text-muted small">⚠️ Weather unavailable.</p>`;
  }
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

/* ── Mandi ───────────────────────────────────────────────── */
let _mandiRaw = [];

async function loadMandi() {
  const wrap = document.getElementById("mandiTable");
  if (wrap) wrap.innerHTML = `<div class="p-3"><span class="spinner-border spinner-border-sm me-2"></span>Loading…</div>`;
  try {
    const res  = await fetch("/api/mandi");
    _mandiRaw  = await res.json();
    renderMandiTable(_mandiRaw);
  } catch {
    if (wrap) wrap.innerHTML = `<p class="text-muted small p-3">⚠️ Could not load prices.</p>`;
  }
}

function filterMandi(q) {
  if (!q) return renderMandiTable(_mandiRaw);
  renderMandiTable(_mandiRaw.filter(p => p.crop.toLowerCase().includes(q.toLowerCase())));
}

function renderMandiTable(prices) {
  const wrap = document.getElementById("mandiTable");
  if (!wrap || !prices.length) return;
  const rows = prices.map(p => {
    const tc = p.trend.includes("↑") ? "km-trend-up" : p.trend.includes("↓") ? "km-trend-down" : "km-trend-flat";
    return `<tr>
      <td class="fw-semibold">${p.crop}</td>
      <td>₹${p.modal_price}</td>
      <td class="${tc}">${p.trend}</td>
      <td style="font-size:.75rem;color:var(--km-muted)">${p.mandi.split(" ")[0]}</td>
    </tr>`;
  }).join("");
  wrap.innerHTML = `
    <table class="km-mandi-table">
      <thead><tr><th>Crop</th><th>₹/Qtl</th><th>Trend</th><th>Mandi</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

/* ── Crop Recommender ─────────────────────────────────────── */
async function loadCrops() {
  const soil   = document.getElementById("soilType")?.value   || "Loamy";
  const season = document.getElementById("seasonType")?.value || "";
  try {
    const res  = await fetch(`/api/crops?soil=${encodeURIComponent(soil)}&season=${encodeURIComponent(season)}`);
    const data = await res.json();
    const bc   = { Kharif:"success", Rabi:"primary", Zaid:"warning" }[data.season] || "secondary";
    const chips = data.recommended_crops.map(c => `<span class="km-crop-chip">🌱 ${c}</span>`).join("");
    const tips  = data.tips.map(t => `<li>${t}</li>`).join("");
    const el    = document.getElementById("cropResults");
    if (el) el.innerHTML = `
      <div class="d-flex gap-2 align-items-center mb-2">
        <span class="badge bg-${bc}">${data.season}</span>
        <span class="text-muted small">${data.soil_type}</span>
      </div>
      <div class="mb-2">${chips}</div>
      <ul class="mb-0 ps-3" style="font-size:.78rem;color:var(--km-muted)">${tips}</ul>`;
  } catch {}
}
