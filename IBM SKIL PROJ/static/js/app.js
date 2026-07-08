/**
 * Kisan Mitra – Smart Farming Advisor
 * Frontend Application Script
 * ───────────────────────────────────
 * Handles: chat, weather, mandi prices, crop recommendations,
 *          voice I/O, dark mode, geolocation
 */

/* ── State ─────────────────────────────────────────────────────── */
let userLat        = parseFloat(document.cookie.match(/lat=([^;]+)/)?.[1]) || 20.59;
let userLon        = parseFloat(document.cookie.match(/lon=([^;]+)/)?.[1]) || 78.96;
let voiceOutEnabled = false;
let mediaRecorder  = null;
let audioChunks    = [];
let isRecording    = false;

/* ── Init ──────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  // Restore dark mode preference
  if (localStorage.getItem("km-dark") === "1") {
    document.documentElement.setAttribute("data-bs-theme", "dark");
    document.querySelector("#darkToggle i").className = "bi bi-sun-fill";
  }

  // Animate crop growth bar to a season-derived value
  const month  = new Date().getMonth() + 1;
  const pct    = month >= 6 && month <= 9  ? 65
               : month >= 10 || month <= 2 ? 85
               : 45;
  setTimeout(() => {
    document.getElementById("growthBar").style.width = pct + "%";
  }, 500);

  // Geolocation
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        userLat = pos.coords.latitude;
        userLon = pos.coords.longitude;
        document.cookie = `lat=${userLat};path=/;max-age=3600`;
        document.cookie = `lon=${userLon};path=/;max-age=3600`;
        loadWeather();
      },
      () => loadWeather()   // fallback to default coords
    );
  } else {
    loadWeather();
  }

  loadMandi();
  renderPestAlerts();

  // Enter-key in chat (Shift+Enter = newline)
  document.getElementById("chatInput").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});

/* ══════════════════════════════════════════════════════
   WEATHER
══════════════════════════════════════════════════════ */
async function loadWeather() {
  const body = document.getElementById("weatherBody");
  body.innerHTML = `<div class="km-skeleton-block"></div><div class="km-skeleton-block short mt-2"></div>`;

  try {
    const res  = await fetch(`/api/weather?lat=${userLat}&lon=${userLon}`);
    const data = await res.json();
    renderWeather(data);
    renderForecast(data.forecast || []);
    updateHeroBadge(data);
  } catch {
    body.innerHTML = `<p class="text-muted small">⚠️ Could not load weather. Check connection.</p>`;
  }
}

function renderWeather(d) {
  document.getElementById("weatherBody").innerHTML = `
    <div class="km-weather-main mb-2">
      <div class="km-weather-icon">${d.weather_icon}</div>
      <div>
        <div class="km-weather-temp">${d.temperature}°C</div>
        <div class="km-weather-desc">${d.weather_desc} · Feels ${d.feels_like}°C</div>
      </div>
    </div>
    <div class="km-weather-grid">
      <div class="km-weather-item"><i class="bi bi-droplet-fill"></i><span>Humidity <strong>${d.humidity}%</strong></span></div>
      <div class="km-weather-item"><i class="bi bi-wind"></i><span>Wind <strong>${d.wind_speed} km/h</strong></span></div>
      <div class="km-weather-item"><i class="bi bi-cloud-rain-fill"></i><span>Rain <strong>${d.precipitation} mm</strong></span></div>
      <div class="km-weather-item"><i class="bi bi-thermometer-half"></i><span>Soil <strong>${d.soil_temp}°C</strong></span></div>
      <div class="km-weather-item"><i class="bi bi-moisture"></i><span>Moisture <strong>${d.soil_moisture}%</strong></span></div>
      <div class="km-weather-item"><i class="bi bi-clock-fill"></i><span style="font-size:.72rem">${d.updated_at}</span></div>
    </div>`;
}

function renderForecast(forecast) {
  const row = document.getElementById("forecastRow");
  if (!forecast.length) { row.innerHTML = `<p class="text-muted small p-2">Forecast unavailable.</p>`; return; }
  row.innerHTML = forecast.map(f => `
    <div class="km-forecast-card">
      <div class="km-forecast-date">${formatDate(f.date)}</div>
      <div class="km-forecast-icon">${f.icon}</div>
      <div class="km-forecast-temp">${f.temp_max}° / ${f.temp_min}°</div>
      <div style="font-size:.7rem;color:var(--km-muted)">${f.precipitation}mm</div>
    </div>`).join("");
}

function updateHeroBadge(d) {
  document.getElementById("heroBadge").innerHTML =
    `<span>${d.weather_icon}</span> <span>${d.temperature}°C · ${d.weather_desc} · Humidity ${d.humidity}%</span>`;
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-IN", { weekday:"short", day:"numeric", month:"short" });
}

/* ══════════════════════════════════════════════════════
   MANDI PRICES
══════════════════════════════════════════════════════ */
async function loadMandi() {
  const wrap = document.getElementById("mandiTable");
  wrap.innerHTML = `<div class="p-3"><span class="spinner-border spinner-border-sm me-2"></span>Loading prices…</div>`;

  try {
    const res  = await fetch("/api/mandi");
    const data = await res.json();
    renderMandi(data);
  } catch {
    wrap.innerHTML = `<p class="text-muted small p-3">⚠️ Could not load mandi prices.</p>`;
  }
}

function renderMandi(prices) {
  if (!prices.length) return;
  const rows = prices.map(p => {
    const trendClass = p.trend.includes("↑") ? "km-trend-up"
                     : p.trend.includes("↓") ? "km-trend-down"
                     : "km-trend-flat";
    return `<tr>
      <td class="fw-semibold">${p.crop}</td>
      <td>₹${p.modal_price}</td>
      <td class="${trendClass}">${p.trend}</td>
      <td style="font-size:.75rem;color:var(--km-muted)">${p.mandi.split(" ")[0]}</td>
    </tr>`;
  }).join("");

  document.getElementById("mandiTable").innerHTML = `
    <table class="km-mandi-table">
      <thead><tr><th>Crop</th><th>₹/Qtl</th><th>Trend</th><th>Mandi</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

/* ══════════════════════════════════════════════════════
   CROP RECOMMENDER
══════════════════════════════════════════════════════ */
async function loadCrops() {
  const soil   = document.getElementById("soilType").value;
  const season = document.getElementById("seasonType").value;
  const res    = await fetch(`/api/crops?soil=${encodeURIComponent(soil)}&season=${encodeURIComponent(season)}`);
  const data   = await res.json();

  const seasonColors = { Kharif:"success", Rabi:"primary", Zaid:"warning" };
  const bc = seasonColors[data.season] || "secondary";

  const chips = data.recommended_crops.map(c =>
    `<span class="km-crop-chip">🌱 ${c}</span>`).join("");

  const tips = data.tips.map(t => `<li>${t}</li>`).join("");

  document.getElementById("cropResults").innerHTML = `
    <div class="d-flex align-items-center gap-2 mb-2">
      <span class="badge bg-${bc} km-season-badge">${data.season} Season</span>
      <span class="text-muted small">${data.soil_type}</span>
    </div>
    <div class="mb-2">${chips}</div>
    <ul class="mb-0 ps-3" style="font-size:.8rem;color:var(--km-muted)">${tips}</ul>`;
}

/* ══════════════════════════════════════════════════════
   PEST ALERTS (static curated list)
══════════════════════════════════════════════════════ */
const PEST_DATA = [
  { name:"Fall Armyworm",       crop:"Maize",   desc:"Window-pane leaf feeding; use Spinetoram 11.7% SC @ 0.5 ml/L.", severity:"high" },
  { name:"Tomato Leaf Curl Virus", crop:"Tomato", desc:"Whitefly-transmitted; use yellow sticky traps + neem oil 3%.", severity:"high" },
  { name:"Rice Blast",          crop:"Rice",    desc:"Diamond-shaped lesions; spray Tricyclazole 75% WP @ 0.6 g/L.",  severity:"medium" },
  { name:"Cotton Bollworm",     crop:"Cotton",  desc:"Use pheromone traps @ 5/ha; spray Emamectin 5% SG @ 0.4 g/L.", severity:"high" },
  { name:"Aphids",              crop:"Mustard", desc:"Spray dimethoate 30 EC @ 1 ml/L or introduce ladybird beetles.",severity:"low" },
  { name:"Helicoverpa",         crop:"Chickpea",desc:"Pheromone traps + HNPV spray @ 250 LE/ha.",                     severity:"medium" },
];

function renderPestAlerts() {
  const colors = { high:"#dc2626", medium:"#ea580c", low:"#16a34a" };
  document.getElementById("pestAlerts").innerHTML = PEST_DATA.map(p => `
    <div class="col-md-6 col-xl-4">
      <div class="km-pest-item" style="border-left-color:${colors[p.severity]}">
        <div class="pest-name">🐛 ${p.name}</div>
        <div class="pest-crop">Affected: <strong>${p.crop}</strong> · <span style="color:${colors[p.severity]};text-transform:capitalize">${p.severity} risk</span></div>
        <div style="font-size:.8rem;margin-top:.25rem">${p.desc}</div>
      </div>
    </div>`).join("");
}

/* ══════════════════════════════════════════════════════
   CHATBOT
══════════════════════════════════════════════════════ */
async function sendMessage() {
  const input   = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message) return;

  appendUserMessage(message);
  input.value = "";

  const typingId = appendTypingIndicator();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        language:  document.getElementById("langSelect").value,
        lat:       userLat,
        lon:       userLon,
        voice_out: voiceOutEnabled,
      }),
    });
    const data = await res.json();
    removeTypingIndicator(typingId);

    if (data.error) {
      appendBotMessage("⚠️ " + data.error, [], null);
    } else {
      appendBotMessage(data.answer, data.sources || [], data.audio_url);
    }
  } catch (err) {
    removeTypingIndicator(typingId);
    appendBotMessage("⚠️ Could not connect to the server. Please try again.", [], null);
  }
}

function sendSuggestion(btn) {
  document.getElementById("chatInput").value = btn.textContent;
  sendMessage();
}

function appendUserMessage(text) {
  const lang = document.getElementById("langSelect").value;
  const initials = lang === "hi" ? "क" : lang === "mr" ? "श" : "F";
  const div = document.createElement("div");
  div.className = "km-msg km-msg-user";
  div.innerHTML = `
    <div class="km-msg-avatar">${initials}</div>
    <div class="km-msg-bubble">${escapeHtml(text)}</div>`;
  appendToChat(div);
}

function appendBotMessage(text, sources, audioUrl) {
  const formatted = formatBotText(text);
  const sourceHtml = sources.length
    ? `<div class="km-msg-source">📎 ${sources.map(s => `[${escapeHtml(s)}]`).join(" ")}</div>`
    : "";
  const audioHtml = audioUrl
    ? `<audio class="km-audio" controls src="${audioUrl}"></audio>`
    : "";

  const div = document.createElement("div");
  div.className = "km-msg km-msg-bot";
  div.innerHTML = `
    <div class="km-msg-avatar">🌾</div>
    <div>
      <div class="km-msg-bubble">${formatted}${audioHtml}</div>
      ${sourceHtml}
    </div>`;
  appendToChat(div);
}

function appendTypingIndicator() {
  const id  = "typing-" + Date.now();
  const div = document.createElement("div");
  div.id        = id;
  div.className = "km-msg km-msg-bot km-typing";
  div.innerHTML = `
    <div class="km-msg-avatar">🌾</div>
    <div class="km-msg-bubble">
      <span class="km-typing-dot"></span>
      <span class="km-typing-dot"></span>
      <span class="km-typing-dot"></span>
    </div>`;
  appendToChat(div);
  return id;
}

function removeTypingIndicator(id) {
  document.getElementById(id)?.remove();
}

function appendToChat(el) {
  const body = document.getElementById("chatBody");
  body.appendChild(el);
  body.scrollTop = body.scrollHeight;
}

function formatBotText(text) {
  // Markdown-lite: bold, bullets, source tags
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\[Source:([^\]]+)\]/g,
      `<span class="badge bg-success-subtle text-success ms-1" style="font-size:.7rem">📎$1</span>`)
    .replace(/^  • (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)+/gs, s => `<ul class="mb-1 ps-3">${s}</ul>`)
    .replace(/\n/g, "<br>");
}

function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
            .replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}

async function clearHistory() {
  await fetch("/api/clear_history", { method: "POST" });
  const body = document.getElementById("chatBody");
  body.innerHTML = `
    <div class="km-msg km-msg-bot">
      <div class="km-msg-avatar">🌾</div>
      <div class="km-msg-bubble">Chat history cleared. How can I help you? 🌾</div>
    </div>`;
}

/* ══════════════════════════════════════════════════════
   VOICE I/O
══════════════════════════════════════════════════════ */
function toggleVoiceOut() {
  voiceOutEnabled = !voiceOutEnabled;
  const btn = document.getElementById("voiceOutToggle");
  btn.classList.toggle("btn-success", voiceOutEnabled);
  btn.title = voiceOutEnabled ? "Voice reply ON" : "Voice reply OFF";
}

async function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    await startRecording();
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks   = [];

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop          = sendAudioToServer;

    mediaRecorder.start();
    isRecording = true;

    const btn = document.getElementById("micBtn");
    btn.classList.add("recording");
    btn.title = "Stop recording";
  } catch (err) {
    alert("Microphone access denied. Please allow mic permissions.");
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
  }
  isRecording = false;
  const btn = document.getElementById("micBtn");
  btn.classList.remove("recording");
  btn.title = "Voice input";
}

async function sendAudioToServer() {
  const blob     = new Blob(audioChunks, { type: "audio/wav" });
  const formData = new FormData();
  formData.append("audio",    blob, "recording.wav");
  formData.append("language", document.getElementById("langSelect").value);

  appendBotMessage("🎤 Processing your voice input…", [], null);

  try {
    const res  = await fetch("/api/voice", { method: "POST", body: formData });
    const data = await res.json();

    if (data.transcript) {
      document.getElementById("chatInput").value = data.transcript;
      // Remove the "processing" message and send
      const msgs = document.querySelectorAll(".km-msg-bot");
      msgs[msgs.length - 1]?.remove();
      sendMessage();
    } else {
      appendBotMessage("⚠️ Could not transcribe audio. Please try again or type your question.", [], null);
    }
  } catch {
    appendBotMessage("⚠️ Voice transcription failed. Please check your connection.", [], null);
  }
}

/* ══════════════════════════════════════════════════════
   DARK MODE
══════════════════════════════════════════════════════ */
document.getElementById("darkToggle").addEventListener("click", () => {
  const html     = document.documentElement;
  const isDark   = html.getAttribute("data-bs-theme") === "dark";
  const icon     = document.querySelector("#darkToggle i");

  if (isDark) {
    html.setAttribute("data-bs-theme", "light");
    icon.className = "bi bi-moon-stars-fill";
    localStorage.setItem("km-dark", "0");
  } else {
    html.setAttribute("data-bs-theme", "dark");
    icon.className = "bi bi-sun-fill";
    localStorage.setItem("km-dark", "1");
  }
});
