/**
 * diseases.js  –  Pest & Disease encyclopedia page
 */

let _allDiseases = [];

document.addEventListener("DOMContentLoaded", loadDiseases);

async function loadDiseases() {
  const grid = document.getElementById("diseaseGrid");
  try {
    const res = await fetch("/api/diseases");
    _allDiseases = await res.json();
    renderDiseaseGrid(_allDiseases);
  } catch {
    grid.innerHTML = `<div class="col-12"><p class="text-muted">⚠️ Could not load disease database.</p></div>`;
  }
}

function renderDiseaseGrid(diseases) {
  const grid = document.getElementById("diseaseGrid");
  if (!diseases.length) {
    grid.innerHTML = `<div class="col-12 text-center py-4 text-muted">No results found.</div>`;
    return;
  }

  const sevColor = { High: "#dc2626", Medium: "#ea580c", Low: "#16a34a" };
  const sevBadge = { High: "danger", Medium: "warning", Low: "success" };
  const typeIcon = { Pest: "🐛", Fungal: "🍄", Virus: "🦠", Bacterial: "🧫" };

  grid.innerHTML = diseases.map(d => `
    <div class="col-md-6 col-xl-4 disease-item"
         data-severity="${d.severity}" data-crop="${d.crop}">
      <div class="km-disease-card" onclick="openModal(${d.id})" style="cursor:pointer">
        <div class="d-flex align-items-start gap-3 mb-2">
          <div class="km-disease-icon">${d.icon}</div>
          <div class="flex-grow-1">
            <div class="fw-bold" style="font-size:.92rem">${d.name}</div>
            <div class="text-muted" style="font-size:.78rem;font-style:italic">${d.scientific}</div>
          </div>
          <span class="badge bg-${sevBadge[d.severity] || 'secondary'}-subtle text-${sevBadge[d.severity] || 'secondary'}">
            ${d.severity}
          </span>
        </div>
        <div class="d-flex gap-2 flex-wrap mb-2">
          <span class="km-crop-chip">🌾 ${d.crop}</span>
          <span class="km-crop-chip" style="background:var(--km-sky-pale)">${typeIcon[d.type] || '🔬'} ${d.type}</span>
        </div>
        <p class="text-muted mb-2" style="font-size:.8rem;line-height:1.5;-webkit-line-clamp:3;overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical">
          ${d.symptoms}
        </p>
        <div class="text-success" style="font-size:.78rem;font-weight:600">
          Click to view full details + controls →
        </div>
      </div>
    </div>`).join("");
}

/* ── Filters ─────────────────────────────────────────────── */
function filterDiseases(q) {
  const ql = q.toLowerCase();
  const filtered = _allDiseases.filter(d =>
    d.name.toLowerCase().includes(ql) ||
    d.crop.toLowerCase().includes(ql) ||
    d.symptoms.toLowerCase().includes(ql)
  );
  renderDiseaseGrid(filtered);
}

function filterBySeverity(sev) {
  renderDiseaseGrid(sev ? _allDiseases.filter(d => d.severity === sev) : _allDiseases);
}

function filterByCrop(crop) {
  renderDiseaseGrid(crop ? _allDiseases.filter(d => d.crop === crop) : _allDiseases);
}

/* ── Detail Modal ─────────────────────────────────────────── */
function openModal(id) {
  const d = _allDiseases.find(x => x.id === id);
  if (!d) return;

  const sevColor = { High: "#dc2626", Medium: "#ea580c", Low: "#16a34a" };
  const col = sevColor[d.severity] || "#888";

  document.getElementById("modalTitle").innerHTML =
    `${d.icon} ${d.name} <small class="text-muted fw-normal" style="font-size:.8rem">(${d.scientific})</small>`;
  document.getElementById("modalHeader").style.borderBottom = `3px solid ${col}`;

  document.getElementById("modalBody").innerHTML = `
    <div class="d-flex gap-2 flex-wrap mb-3">
      <span class="badge text-bg-secondary">🌾 ${d.crop}</span>
      <span class="badge" style="background:${col}">${d.severity} Risk</span>
      <span class="badge text-bg-secondary">${d.type}</span>
    </div>

    <div class="km-modal-section">
      <div class="km-modal-label">🔍 Symptoms</div>
      <p class="mb-0">${d.symptoms}</p>
    </div>

    <div class="km-modal-section">
      <div class="km-modal-label">🌬️ How it Spreads</div>
      <p class="mb-0">${d.spread}</p>
    </div>

    <div class="row g-3 mt-1">
      <div class="col-md-6">
        <div class="km-modal-section h-100" style="border-left:3px solid #dc2626">
          <div class="km-modal-label text-danger">💊 Chemical Control</div>
          <p class="mb-0 small">${d.chemical_control}</p>
        </div>
      </div>
      <div class="col-md-6">
        <div class="km-modal-section h-100" style="border-left:3px solid #16a34a">
          <div class="km-modal-label text-success">🌿 Organic / Biological Control</div>
          <p class="mb-0 small">${d.organic_control}</p>
        </div>
      </div>
    </div>

    <div class="km-modal-section mt-3">
      <div class="km-modal-label">🛡️ Prevention</div>
      <p class="mb-0">${d.prevention}</p>
    </div>`;

  document.getElementById("modalAskBtn").href =
    `/chat?q=${encodeURIComponent("Tell me more about " + d.name + " in " + d.crop)}`;

  new bootstrap.Modal(document.getElementById("diseaseModal")).show();
}
