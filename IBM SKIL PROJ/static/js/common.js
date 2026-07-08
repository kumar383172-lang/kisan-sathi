/**
 * common.js  –  Shared across all pages
 * Dark mode, language persistence, geo-detection
 */

/* ── Dark mode ─────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("km-dark") === "1") {
    document.documentElement.setAttribute("data-bs-theme", "dark");
    const icon = document.querySelector("#darkToggle i");
    if (icon) icon.className = "bi bi-sun-fill";
  }

  const langSelect = document.getElementById("langSelect");
  if (langSelect) {
    const saved = localStorage.getItem("km-lang");
    if (saved) langSelect.value = saved;
    langSelect.addEventListener("change", () => {
      localStorage.setItem("km-lang", langSelect.value);
      // sync chat page lang select if present
      const cls = document.getElementById("chatLangSelect");
      if (cls) cls.value = langSelect.value;
    });
  }
});

const darkToggle = document.getElementById("darkToggle");
if (darkToggle) {
  darkToggle.addEventListener("click", () => {
    const html  = document.documentElement;
    const isDark = html.getAttribute("data-bs-theme") === "dark";
    const icon  = darkToggle.querySelector("i");
    if (isDark) {
      html.setAttribute("data-bs-theme", "light");
      if (icon) icon.className = "bi bi-moon-stars-fill";
      localStorage.setItem("km-dark", "0");
    } else {
      html.setAttribute("data-bs-theme", "dark");
      if (icon) icon.className = "bi bi-sun-fill";
      localStorage.setItem("km-dark", "1");
    }
  });
}

/* ── Shared geo state ─────────────────────────────────────── */
window.userLat = parseFloat(localStorage.getItem("km-lat")) || 20.59;
window.userLon = parseFloat(localStorage.getItem("km-lon")) || 78.96;

function detectLocation(onSuccess) {
  if (!navigator.geolocation) { if (onSuccess) onSuccess(); return; }
  navigator.geolocation.getCurrentPosition(
    pos => {
      window.userLat = pos.coords.latitude;
      window.userLon = pos.coords.longitude;
      localStorage.setItem("km-lat", window.userLat);
      localStorage.setItem("km-lon", window.userLon);
      document.cookie = `lat=${window.userLat};path=/;max-age=3600`;
      document.cookie = `lon=${window.userLon};path=/;max-age=3600`;
      if (onSuccess) onSuccess();
    },
    () => { if (onSuccess) onSuccess(); }
  );
}

/* ── Shared weather renderers (used by dashboard + landing) ─ */
function renderWeatherBody(d, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
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

function renderForecastRow(forecast, containerId) {
  const el = document.getElementById(containerId);
  if (!el || !forecast.length) return;
  el.innerHTML = forecast.map(f => `
    <div class="km-forecast-card">
      <div class="km-forecast-date">${formatDate(f.date)}</div>
      <div class="km-forecast-icon">${f.icon}</div>
      <div class="km-forecast-temp">${f.temp_max}° / ${f.temp_min}°</div>
      <div style="font-size:.7rem;color:var(--km-muted)">${f.precipitation}mm</div>
    </div>`).join("");
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString("en-IN", { weekday:"short", day:"numeric", month:"short" });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}

function formatBotText(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/\[Source:([^\]]+)\]/g,
      `<span class="km-source-badge">📎$1</span>`)
    .replace(/^[-•] (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, s => `<ul class="mb-1 ps-3">${s}</ul>`)
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>");
}
