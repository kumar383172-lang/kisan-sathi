/**
 * chat.js  –  Kisan Mitra Copilot-style chat
 * ─────────────────────────────────────────────
 * Features:
 *  - SSE token-streaming with real-time rendering
 *  - Full Markdown + syntax highlighting via marked + highlight.js
 *  - Copy-to-clipboard on every message
 *  - Auto-resizing textarea
 *  - Conversation sidebar with history
 *  - Voice in/out
 *  - Geolocation-aware
 */

/* ── Configure marked ───────────────────────────────────────── */
if (typeof marked !== "undefined") {
  marked.setOptions({
    breaks:    true,
    gfm:       true,
    highlight: (code, lang) => {
      if (typeof hljs !== "undefined" && lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      return typeof hljs !== "undefined" ? hljs.highlightAuto(code).value : code;
    },
  });
}

/* ── State ──────────────────────────────────────────────────── */
let voiceOutEnabled  = false;
let mediaRecorder    = null;
let audioChunks      = [];
let isRecording      = false;
let isSending        = false;
let currentStreamCtl = null;   // AbortController for active stream
let chatSessions     = JSON.parse(localStorage.getItem("km-sessions") || "[]");
let activeSession    = null;

/* ── Init ───────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  detectLocation();
  loadStatus();
  renderSidebar();
  syncLang();

  const inp = document.getElementById("chatInput");
  if (inp) {
    inp.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    inp.addEventListener("input", () => autoResize(inp));
  }
});

function syncLang() {
  const nav = document.getElementById("langSelect");
  const cl  = document.getElementById("chatLangSelect");
  if (!nav || !cl) return;
  const saved = localStorage.getItem("km-lang");
  if (saved) { nav.value = saved; cl.value = saved; }
  cl.addEventListener("change", () => {
    nav.value = cl.value;
    localStorage.setItem("km-lang", cl.value);
  });
}

async function loadStatus() {
  try {
    const r = await fetch("/api/status");
    const d = await r.json();
    const el = document.getElementById("cpModelName");
    if (el) el.textContent = d.model ? d.model.split("/").pop() : "IBM Granite";
    const pb = document.getElementById("cpPoweredBy");
    if (pb) pb.textContent = d.ibm_configured
      ? `IBM Watsonx Granite · ${d.model}`
      : "Kisan Mitra AI · Configure IBM credentials for full power";
  } catch {}
}

/* ── Auto-resize textarea ──────────────────────────────────── */
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 200) + "px";
}

/* ════════════════════════════════════════════════════
   SEND MESSAGE (SSE streaming)
════════════════════════════════════════════════════ */
async function sendMessage() {
  if (isSending) { stopStream(); return; }

  const input   = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message) return;

  // Hide welcome, show suggestions
  document.getElementById("cpWelcome")?.classList.add("d-none");
  document.getElementById("cpSuggestions")?.classList.remove("d-none");

  isSending = true;
  setStatus("Thinking…", true);
  setSendBtn("stop");

  appendUserMessage(message);
  input.value = "";
  input.style.height = "auto";

  // Save to sidebar history
  if (!activeSession) {
    activeSession = { id: Date.now(), title: message.slice(0, 40), messages: [] };
    chatSessions.unshift(activeSession);
    renderSidebar();
  }
  activeSession.messages.push({ role: "user", content: message });

  // Create bot message container with streaming cursor
  const msgId   = "msg-" + Date.now();
  const bubbleId = "bubble-" + Date.now();
  appendBotMessageShell(msgId, bubbleId);

  currentStreamCtl = new AbortController();

  try {
    const res = await fetch("/api/chat/stream", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        message,
        language:  document.getElementById("chatLangSelect")?.value || "en",
        lat:       window.userLat,
        lon:       window.userLon,
      }),
      signal: currentStreamCtl.signal,
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = "";
    let   rawText = "";
    let   sources = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();  // keep incomplete line

      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload) continue;

        try {
          const evt = JSON.parse(payload);

          if (evt.done) {
            sources = evt.sources || [];
            break;
          }

          if (evt.token) {
            rawText += evt.token;
            // Render markdown progressively — throttled
            renderStreamChunk(bubbleId, rawText);
          }
        } catch {}
      }
    }

    // Final render (ensures last chunk is clean)
    finalizeMessage(msgId, bubbleId, rawText, sources);
    activeSession.messages.push({ role: "assistant", content: rawText });
    saveSessionStorage();

    if (voiceOutEnabled && rawText) {
      triggerTTS(rawText, document.getElementById("chatLangSelect")?.value || "en");
    }

  } catch (err) {
    if (err.name === "AbortError") {
      finalizeMessage(msgId, bubbleId, document.getElementById(bubbleId)?._raw || "(stopped)", []);
    } else {
      finalizeMessage(msgId, bubbleId,
        "⚠️ **Connection error.** Please check your network and try again.", []);
    }
  } finally {
    isSending        = false;
    currentStreamCtl = null;
    setStatus("Ready", false);
    setSendBtn("send");
  }
}

function stopStream() {
  currentStreamCtl?.abort();
}

/* ── Starters / suggestions ────────────────────────────────── */
function sendStarter(btn) {
  document.getElementById("chatInput").value = btn.querySelector(".cp-starter-text").textContent.trim();
  sendMessage();
}
function sendPill(btn) {
  const map = {
    "🌱 Best crop now":   "What is the best crop to grow right now based on current season?",
    "💰 Mandi prices":    "Show me today's mandi prices for major crops",
    "🌤️ Weather today":   "What is the current weather and should I irrigate today?",
    "🐛 Pest alert":      "What are the active pest and disease alerts this season?",
    "🏛️ Govt schemes":   "Tell me about government schemes for farmers",
    "🌿 Organic tips":    "How do I prepare Jeevamrut and other organic inputs?",
  };
  document.getElementById("chatInput").value = map[btn.textContent.trim()] || btn.textContent.trim();
  sendMessage();
}

/* ════════════════════════════════════════════════════
   MESSAGE DOM HELPERS
════════════════════════════════════════════════════ */
function appendUserMessage(text) {
  const now  = timestamp();
  const div  = document.createElement("div");
  div.className = "cp-msg cp-msg-user";
  div.innerHTML = `
    <div class="cp-msg-content">
      <div class="cp-user-bubble">${escapeHtml(text)}</div>
      <div class="cp-msg-meta">${now}</div>
    </div>
    <div class="cp-msg-avatar cp-user-av">
      <i class="bi bi-person-fill"></i>
    </div>`;
  appendToChat(div);
}

function appendBotMessageShell(msgId, bubbleId) {
  const div = document.createElement("div");
  div.id        = msgId;
  div.className = "cp-msg cp-msg-bot";
  div.innerHTML = `
    <div class="cp-msg-avatar cp-bot-av">🌾</div>
    <div class="cp-msg-content">
      <div class="cp-bot-bubble" id="${bubbleId}">
        <span class="cp-cursor"></span>
      </div>
    </div>`;
  appendToChat(div);
}

let _renderTimer = null;
function renderStreamChunk(bubbleId, rawText) {
  const el = document.getElementById(bubbleId);
  if (!el) return;
  el._raw = rawText;

  // Throttle markdown rendering to every 80ms max
  if (_renderTimer) return;
  _renderTimer = setTimeout(() => {
    _renderTimer = null;
    const el2 = document.getElementById(bubbleId);
    if (!el2) return;
    el2.innerHTML = renderMarkdown(el2._raw || rawText) + `<span class="cp-cursor"></span>`;
    highlightCode(el2);
    scrollToBottom();
  }, 80);
}

function finalizeMessage(msgId, bubbleId, rawText, sources) {
  clearTimeout(_renderTimer);
  _renderTimer = null;

  const bubble = document.getElementById(bubbleId);
  if (!bubble) return;

  const md     = renderMarkdown(rawText);
  const srcHtml = sources.length
    ? `<div class="cp-sources">${sources.map(s =>
        `<span class="cp-source-chip">📎 ${escapeHtml(s)}</span>`).join("")}</div>`
    : "";
  const now = timestamp();

  bubble.innerHTML = md;
  highlightCode(bubble);

  // Meta bar: timestamp + copy button
  const metaDiv = document.createElement("div");
  metaDiv.className = "cp-msg-meta d-flex align-items-center gap-2 mt-1";
  metaDiv.innerHTML = `
    <span>${now} · Kisan Mitra</span>
    ${srcHtml}
    <button class="cp-copy-btn ms-auto" onclick="copyMessage(this)" data-text="${escapeAttr(rawText)}" title="Copy">
      <i class="bi bi-clipboard"></i>
    </button>
    <button class="cp-copy-btn" onclick="regenMessage(this)" data-msgid="${msgId}" title="Regenerate">
      <i class="bi bi-arrow-clockwise"></i>
    </button>`;

  const msgEl = document.getElementById(msgId);
  if (msgEl) msgEl.querySelector(".cp-msg-content")?.appendChild(metaDiv);

  scrollToBottom();
}

function appendToChat(el) {
  const body = document.getElementById("chatBody");
  body.appendChild(el);
  scrollToBottom();
}

function scrollToBottom() {
  const body = document.getElementById("chatBody");
  if (body) body.scrollTop = body.scrollHeight;
}

/* ════════════════════════════════════════════════════
   MARKDOWN RENDERING
════════════════════════════════════════════════════ */
function renderMarkdown(text) {
  if (typeof marked === "undefined") return escapeHtml(text).replace(/\n/g,"<br>");
  // Remove [Source: ...] tags from main body (shown separately)
  const clean = text.replace(/\[Source:\s*[^\]]+\]/g, "").trim();
  return marked.parse(clean);
}

function highlightCode(container) {
  if (typeof hljs === "undefined") return;
  container.querySelectorAll("pre code").forEach(block => {
    if (!block.dataset.highlighted) {
      hljs.highlightElement(block);
      block.dataset.highlighted = "1";

      // Add copy button to code blocks
      const pre   = block.parentElement;
      const lang  = block.className.replace("language-","").split(" ")[0] || "code";
      const wrap  = document.createElement("div");
      wrap.className = "cp-code-header";
      wrap.innerHTML = `
        <span class="cp-code-lang">${escapeHtml(lang)}</span>
        <button class="cp-code-copy" onclick="copyCode(this)">
          <i class="bi bi-clipboard me-1"></i>Copy
        </button>`;
      pre.style.position = "relative";
      pre.insertBefore(wrap, block);
    }
  });
}

function copyCode(btn) {
  const code = btn.closest("pre")?.querySelector("code")?.innerText || "";
  navigator.clipboard.writeText(code).then(() => {
    btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Copied!';
    setTimeout(() => { btn.innerHTML = '<i class="bi bi-clipboard me-1"></i>Copy'; }, 2000);
  });
}

function copyMessage(btn) {
  const text = btn.dataset.text || "";
  navigator.clipboard.writeText(text).then(() => {
    btn.innerHTML = '<i class="bi bi-check2"></i>';
    setTimeout(() => { btn.innerHTML = '<i class="bi bi-clipboard"></i>'; }, 2000);
  });
}

function regenMessage(btn) {
  // Re-send the last user message
  const msgs = document.querySelectorAll(".cp-msg-user");
  if (!msgs.length) return;
  const last = msgs[msgs.length - 1].querySelector(".cp-user-bubble")?.textContent?.trim();
  if (!last) return;
  // Remove the bot message to be regenerated
  document.getElementById(btn.dataset.msgid)?.remove();
  document.getElementById("chatInput").value = last;
  sendMessage();
}

/* ════════════════════════════════════════════════════
   SIDEBAR
════════════════════════════════════════════════════ */
let sidebarOpen = true;

function toggleSidebar() {
  sidebarOpen = !sidebarOpen;
  document.getElementById("cpSidebar").classList.toggle("cp-sidebar-hidden", !sidebarOpen);
  document.getElementById("cpMain").classList.toggle("cp-main-full", !sidebarOpen);
}

function renderSidebar() {
  const el = document.getElementById("cpHistory");
  if (!el) return;
  if (!chatSessions.length) {
    el.innerHTML = `<div class="cp-no-history">No conversations yet</div>`;
    return;
  }
  el.innerHTML = chatSessions.slice(0, 20).map(s => `
    <div class="cp-history-item ${s.id === activeSession?.id ? 'active' : ''}"
         onclick="loadSession(${s.id})">
      <i class="bi bi-chat-text me-2 flex-shrink-0"></i>
      <span class="cp-history-title">${escapeHtml(s.title || "New chat")}</span>
      <button class="cp-delete-session" title="Delete this chat"
              onclick="event.stopPropagation(); deleteSession(${s.id})">
        <i class="bi bi-trash3"></i>
      </button>
    </div>`).join("");
}

function deleteSession(id) {
  chatSessions = chatSessions.filter(s => s.id !== id);
  if (activeSession?.id === id) {
    activeSession = null;
    // clear the chat body and show welcome screen
    const body    = document.getElementById("chatBody");
    const welcome = document.getElementById("cpWelcome");
    body.innerHTML = "";
    if (welcome) { welcome.classList.remove("d-none"); body.appendChild(welcome); }
    document.getElementById("cpSuggestions")?.classList.add("d-none");
    // clear server-side session too
    fetch("/api/clear_history", { method: "POST" });
  }
  saveSessionStorage();
  renderSidebar();
}

function loadSession(id) {
  const session = chatSessions.find(s => s.id === id);
  if (!session) return;
  activeSession = session;

  const body = document.getElementById("chatBody");
  document.getElementById("cpWelcome")?.classList.add("d-none");
  document.getElementById("cpSuggestions")?.classList.remove("d-none");

  // Re-render all messages
  const kept = body.querySelector("#cpWelcome");
  body.innerHTML = "";
  if (kept) body.appendChild(kept);

  for (const msg of session.messages) {
    if (msg.role === "user") {
      appendUserMessage(msg.content);
    } else {
      const msgId    = "msg-" + Math.random().toString(36).slice(2);
      const bubbleId = "bubble-" + Math.random().toString(36).slice(2);
      appendBotMessageShell(msgId, bubbleId);
      finalizeMessage(msgId, bubbleId, msg.content, []);
    }
  }
  renderSidebar();
}

function newChat() {
  activeSession = null;
  const body = document.getElementById("chatBody");
  const welcome = document.getElementById("cpWelcome");
  body.innerHTML = "";
  if (welcome) { welcome.classList.remove("d-none"); body.appendChild(welcome); }
  document.getElementById("cpSuggestions")?.classList.add("d-none");
  document.getElementById("chatInput").value = "";
  fetch("/api/clear_history", { method: "POST" });
  renderSidebar();
}

function saveSessionStorage() {
  localStorage.setItem("km-sessions", JSON.stringify(chatSessions.slice(0, 30)));
}

async function clearHistory() {
  // Show confirmation modal instead of wiping immediately
  const modal = document.getElementById("clearHistoryModal");
  if (modal) {
    new bootstrap.Modal(modal).show();
  } else {
    await _doClearHistory();
  }
}

async function _doClearHistory() {
  chatSessions   = [];
  activeSession  = null;
  localStorage.removeItem("km-sessions");
  saveSessionStorage();
  await fetch("/api/clear_history", { method: "POST" });
  newChat();
}

/* ════════════════════════════════════════════════════
   UI HELPERS
════════════════════════════════════════════════════ */
function setStatus(text, busy) {
  const el = document.getElementById("statusText");
  const dot = document.querySelector(".cp-status-dot");
  if (el)  el.textContent = text;
  if (dot) dot.style.background = busy ? "#f59e0b" : "#22c55e";
}

function setSendBtn(mode) {
  const btn = document.getElementById("sendBtn");
  if (!btn) return;
  if (mode === "stop") {
    btn.innerHTML    = '<i class="bi bi-stop-fill"></i>';
    btn.style.background = "#dc2626";
    btn.title        = "Stop generating";
  } else {
    btn.innerHTML    = '<i class="bi bi-arrow-up"></i>';
    btn.style.background = "";
    btn.title        = "Send";
  }
}

function timestamp() {
  return new Date().toLocaleTimeString("en-IN", { hour:"2-digit", minute:"2-digit" });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}

function escapeAttr(str) {
  return (str || "").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}

/* ════════════════════════════════════════════════════
   VOICE OUT
════════════════════════════════════════════════════ */
function toggleVoiceOut() {
  voiceOutEnabled = !voiceOutEnabled;
  const btn = document.getElementById("voiceOutToggle");
  if (!btn) return;
  btn.style.background = voiceOutEnabled ? "var(--cp-accent)" : "";
  btn.style.color      = voiceOutEnabled ? "#fff" : "";
  btn.title            = voiceOutEnabled ? "Voice ON" : "Voice reply";
}

async function triggerTTS(text, lang) {
  try {
    const res  = await fetch("/api/chat", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ message: "__tts__", language: lang, voice_out: true }),
    });
    const data = await res.json();
    if (data.audio_url) {
      const audio = new Audio(data.audio_url);
      audio.play();
    }
  } catch {}
}

/* ════════════════════════════════════════════════════
   VOICE IN
════════════════════════════════════════════════════ */
async function toggleRecording() {
  if (isRecording) stopRecording(); else await startRecording();
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
    if (btn) {
      btn.classList.add("recording");
      btn.title = "Stop recording";
    }
    setStatus("🎤 Recording…", true);
  } catch {
    alert("Microphone access denied. Please allow mic permissions in browser settings.");
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    mediaRecorder.stream?.getTracks().forEach(t => t.stop());
  }
  isRecording = false;
  const btn = document.getElementById("micBtn");
  if (btn) { btn.classList.remove("recording"); btn.title = "Voice input"; }
  setStatus("Processing voice…", true);
}

async function sendAudioToServer() {
  const blob = new Blob(audioChunks, { type: "audio/wav" });
  const fd   = new FormData();
  fd.append("audio",    blob, "recording.wav");
  fd.append("language", document.getElementById("chatLangSelect")?.value || "hi");
  try {
    const res  = await fetch("/api/voice", { method: "POST", body: fd });
    const data = await res.json();
    if (data.transcript) {
      document.getElementById("chatInput").value = data.transcript;
      autoResize(document.getElementById("chatInput"));
      sendMessage();
    } else {
      setStatus("Could not transcribe. Please type.", false);
    }
  } catch {
    setStatus("Voice error.", false);
  }
}
