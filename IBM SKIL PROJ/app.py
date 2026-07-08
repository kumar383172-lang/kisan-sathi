"""
app.py  –  Kisan Mitra Smart Farming Advisor
─────────────────────────────────────────────
Universal LLM + Farming specialist:
  • Groq (free tier)  – Llama 3.3 70B / Mixtral    [PRIMARY]
  • Google Gemini (free tier) – Gemini 1.5 Flash    [FALLBACK 1]
  • IBM Watsonx.ai Granite  (SDK → REST fallback)   [FALLBACK 2]
  • SSE token-streaming endpoint (/api/chat/stream)
  • Standard JSON endpoint (/api/chat)
  • DuckDuckGo web-search context enrichment
  • RAG from FAISS vector store
  • General-purpose: answers ANY question
"""

import os, re, time, json, logging, requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, session, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv(override=True)   # override=True ensures .env always wins over stale OS env vars

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "kisan-dev-secret-xyz")
CORS(app)

# ─────────────────────────────────────────────────────────────
# ── FREE LLM #1: Groq  (https://console.groq.com – free tier)
#    Models: llama-3.3-70b-versatile, mixtral-8x7b-32768
#    Rate limit free tier: 14 400 req-tokens/min, 30 req/min
# ─────────────────────────────────────────────────────────────
def _has_groq() -> bool:
    return bool(os.getenv("GROQ_API_KEY", "").strip())

def call_groq(messages: list, max_tokens: int = 1200) -> str | None:
    """Call Groq Chat Completions API (OpenAI-compatible)."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model":       model,
                "messages":    messages,
                "max_tokens":  max_tokens,
                "temperature": 0.6,
                "top_p":       0.95,
                "stream":      False,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None

def stream_groq(messages: list):
    """Generator: yields text tokens from Groq streaming endpoint."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model":       model,
                "messages":    messages,
                "max_tokens":  1200,
                "temperature": 0.6,
                "top_p":       0.95,
                "stream":      True,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            stream=True,
            timeout=60,
        )
        resp.raise_for_status()
        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if line.startswith("data: "):
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
    except Exception as e:
        logger.error(f"Groq stream error: {e}")


# ─────────────────────────────────────────────────────────────
# ── FREE LLM #2: Google Gemini  (https://aistudio.google.com – free)
#    Model: gemini-1.5-flash  (15 rpm free, 1 M ctx)
# ─────────────────────────────────────────────────────────────
def _has_gemini() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())

def call_gemini(messages: list, max_tokens: int = 1200) -> str | None:
    """Call Google Gemini generateContent REST API."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    # Convert OpenAI-style messages → Gemini contents format
    contents = []
    system_text = ""
    for m in messages:
        if m["role"] == "system":
            system_text = m["content"]
        elif m["role"] == "user":
            text = (system_text + "\n\n" + m["content"]) if system_text else m["content"]
            contents.append({"role": "user",  "parts": [{"text": text}]})
            system_text = ""
        elif m["role"] == "assistant":
            contents.append({"role": "model", "parts": [{"text": m["content"]}]})
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json={
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature":     0.6,
                    "topP":            0.95,
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return None

def stream_gemini(messages: list):
    """Generator: yields text tokens from Gemini streamGenerateContent."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    contents = []
    system_text = ""
    for m in messages:
        if m["role"] == "system":
            system_text = m["content"]
        elif m["role"] == "user":
            text = (system_text + "\n\n" + m["content"]) if system_text else m["content"]
            contents.append({"role": "user",  "parts": [{"text": text}]})
            system_text = ""
        elif m["role"] == "assistant":
            contents.append({"role": "model", "parts": [{"text": m["content"]}]})
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={api_key}",
            json={
                "contents": contents,
                "generationConfig": {"maxOutputTokens": 1200, "temperature": 0.6, "topP": 0.95},
            },
            stream=True,
            timeout=60,
        )
        resp.raise_for_status()
        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if line.startswith("data: "):
                payload = line[6:].strip()
                if not payload or payload == "[DONE]":
                    continue
                try:
                    chunk = json.loads(payload)
                    text = (chunk.get("candidates", [{}])[0]
                                  .get("content", {})
                                  .get("parts", [{}])[0]
                                  .get("text", ""))
                    if text:
                        yield text
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
    except Exception as e:
        logger.error(f"Gemini stream error: {e}")


# ─────────────────────────────────────────────────────────────
# ── Helper: build OpenAI-style messages list from prompt parts
# ─────────────────────────────────────────────────────────────
def _build_messages(context: str, history_text: str, question: str) -> list:
    """Convert Kisan Mitra prompt components into chat-messages format."""
    from agent_instructions import SYSTEM_PROMPT as _SP
    system_body = (
        "You are Kisan Mitra, a highly capable AI assistant with deep expertise in "
        "Indian agriculture (crops, soil, seasons, irrigation, organic farming), "
        "pest & disease management (ICAR guidelines), live mandi prices, government "
        "schemes, and weather interpretation. You can also answer any general "
        "knowledge, math, coding, creative or translation question. "
        "Use Markdown formatting. Cite sources as [Source: name]. "
        "Respond in the same language the user writes in. Be complete and thorough.\n\n"
        f"Live Context:\n{context}\n\n"
        f"Conversation so far:\n{history_text or 'None'}"
    )
    return [
        {"role": "system",    "content": system_body},
        {"role": "user",      "content": question},
    ]


# ─────────────────────────────────────────────────────────────
# IBM Watsonx IAM token
# ─────────────────────────────────────────────────────────────
_iam_token  = None
_iam_expiry = 0

def get_iam_token() -> str | None:
    global _iam_token, _iam_expiry
    if _iam_token and time.time() < _iam_expiry - 60:
        return _iam_token
    api_key = os.getenv("IBM_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        resp = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        resp.raise_for_status()
        j           = resp.json()
        _iam_token  = j["access_token"]
        _iam_expiry = time.time() + j.get("expires_in", 3600)
        return _iam_token
    except Exception as e:
        logger.error(f"IAM token error: {e}")
        return None

def has_ibm_credentials() -> bool:
    return bool(os.getenv("IBM_API_KEY","").strip() and os.getenv("IBM_PROJECT_ID","").strip())

# ─────────────────────────────────────────────────────────────
# Watsonx SDK model (cached)
# ─────────────────────────────────────────────────────────────
_watsonx_model      = None
_vector_store_ready = False   # tracks whether index has been rebuilt for this run

def get_watsonx_model():
    global _watsonx_model
    if _watsonx_model is not None:
        return _watsonx_model
    if not has_ibm_credentials():
        return None
    try:
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params
        from ibm_watsonx_ai import Credentials
        creds  = Credentials(url=os.getenv("IBM_WATSONX_URL","https://us-south.ml.cloud.ibm.com"),
                             api_key=os.getenv("IBM_API_KEY",""))
        params = {
            Params.MAX_NEW_TOKENS:     1200,
            Params.TEMPERATURE:        0.6,
            Params.TOP_P:              0.95,
            Params.REPETITION_PENALTY: 1.1,
            Params.STOP_SEQUENCES:     ["<|user|>", "<|system|>"],
        }
        _watsonx_model = ModelInference(
            model_id=os.getenv("WATSONX_MODEL_ID","ibm/granite-13b-chat-v2"),
            credentials=creds,
            project_id=os.getenv("IBM_PROJECT_ID",""),
            params=params,
        )
        logger.info("Watsonx SDK loaded OK")
    except Exception as e:
        logger.error(f"Watsonx SDK error: {e}")
        _watsonx_model = None
    return _watsonx_model


# ─────────────────────────────────────────────────────────────
# Watsonx REST generate (non-streaming)
# ─────────────────────────────────────────────────────────────
def call_watsonx_rest(prompt: str, max_tokens: int = 1200) -> str | None:
    token      = get_iam_token()
    project_id = os.getenv("IBM_PROJECT_ID","").strip()
    base_url   = os.getenv("IBM_WATSONX_URL","https://us-south.ml.cloud.ibm.com")
    model_id   = os.getenv("WATSONX_MODEL_ID","ibm/granite-13b-chat-v2")
    if not token or not project_id:
        return None
    try:
        resp = requests.post(
            f"{base_url}/ml/v1/text/generation?version=2023-05-29",
            json={
                "model_id":   model_id,
                "project_id": project_id,
                "input":      prompt,
                "parameters": {
                    "max_new_tokens":      max_tokens,
                    "temperature":         0.6,
                    "top_p":               0.95,
                    "repetition_penalty":  1.1,
                    "stop_sequences":      ["<|user|>", "<|system|>", "<|end|>"],
                },
            },
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=40,
        )
        if resp.status_code == 403:
            logger.error(
                f"Watsonx 403 Forbidden — API key user is NOT a member of project {project_id}. "
                f"Fix: open Watsonx.ai > project > Manage > Access Control > add your IBM account as Admin."
            )
            return None
        resp.raise_for_status()
        return resp.json()["results"][0]["generated_text"].strip()
    except Exception as e:
        logger.error(f"Watsonx REST error: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# Watsonx REST streaming (yields text chunks via SSE)
# ─────────────────────────────────────────────────────────────
def stream_watsonx_rest(prompt: str):
    """Generator: yields text fragments from Watsonx streaming endpoint."""
    token      = get_iam_token()
    project_id = os.getenv("IBM_PROJECT_ID","").strip()
    base_url   = os.getenv("IBM_WATSONX_URL","https://us-south.ml.cloud.ibm.com")
    model_id   = os.getenv("WATSONX_MODEL_ID","ibm/granite-13b-chat-v2")
    if not token or not project_id:
        return

    try:
        resp = requests.post(
            f"{base_url}/ml/v1/text/generation_stream?version=2023-05-29",
            json={
                "model_id":   model_id,
                "project_id": project_id,
                "input":      prompt,
                "parameters": {
                    "max_new_tokens":     1200,
                    "temperature":        0.6,
                    "top_p":              0.95,
                    "repetition_penalty": 1.1,
                    "stop_sequences":     ["<|user|>", "<|system|>", "<|end|>"],
                },
            },
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            stream=True,
            timeout=60,
        )
        resp.raise_for_status()
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    token_text = (chunk.get("results", [{}])[0]
                                       .get("generated_text", ""))
                    if token_text:
                        yield token_text
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue
    except Exception as e:
        logger.error(f"Watsonx stream error: {e}")


# ─────────────────────────────────────────────────────────────
# DuckDuckGo web-search context
# ─────────────────────────────────────────────────────────────
def web_search_context(query: str) -> str:
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=6,
        )
        data  = resp.json()
        parts = []
        if data.get("AbstractText"):
            parts.append(f"Web summary: {data['AbstractText']}")
        for r in data.get("RelatedTopics", [])[:3]:
            if isinstance(r, dict) and r.get("Text"):
                parts.append(f"Related: {r['Text']}")
        return "\n".join(parts)
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────
# RAG vector store
# ─────────────────────────────────────────────────────────────
_vector_store = None

def get_vector_store():
    global _vector_store, _vector_store_ready
    if _vector_store is None:
        try:
            from rag.knowledge_base import load_vector_store
            # Force rebuild so any newly added KB chunks are always indexed
            _vector_store = load_vector_store(force_rebuild=True)
            _vector_store_ready = True
        except Exception as e:
            logger.error(f"Vector store load error: {e}")
    return _vector_store


# ─────────────────────────────────────────────────────────────
# Services
# ─────────────────────────────────────────────────────────────
from services.weather      import get_weather, weather_to_text
from services.mandi_prices import get_mandi_prices, prices_to_text
from services.crop_advisor import recommend_crops, get_season
from services.voice        import speech_to_text, text_to_speech
from agent_instructions    import SYSTEM_PROMPT


# ─────────────────────────────────────────────────────────────
# Context assembly
# ─────────────────────────────────────────────────────────────
_AGRI_KEYWORDS = {
    # seasons / crops
    "crop","farm","soil","weather","rain","mandi","price","pest","disease",
    "seed","fertilizer","fertiliser","irrigation","harvest","sow","plant",
    "wheat","rice","cotton","tomato","onion","potato","maize","sugarcane",
    "kharif","rabi","zaid","yield",
    # organic inputs & preparations
    "organic","jeevamrut","beejamrut","panchagavya","vermicompost","compost",
    "neem","biofertiliser","biofertilizer","green manure","mulch","biochar",
    "trichoderma","azotobacter","rhizobium","azolla","amrit pani","dashparni",
    "agniastra","brahmastra","fpj","faa","fish amino","wood vinegar","wca",
    "lab serum","pheromone","sticky trap","bt spray","bordeaux","nske",
    "prepare","preparation","how to make","how do i","recipe","spray",
    # schemes
    "scheme","yojana","pm kisan","pmfby","kcc","subsidy","insurance",
    # Hindi / regional keywords
    "खेती","फसल","मौसम","भाव","बारिश","मिट्टी","खाद","कीट","रोग",
    "जीवामृत","बीजामृत","पंचगव्य","नीम","जैविक",
}

def _is_farming_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in _AGRI_KEYWORDS)

def build_context(query: str, lat: float, lon: float) -> str:
    parts = []

    # Always include RAG chunks (small, relevant)
    store = get_vector_store()
    if store and _is_farming_query(query):
        try:
            from rag.knowledge_base import retrieve_context
            chunk = retrieve_context(query, store, k=3)
            if chunk:
                parts.append(chunk)
        except Exception:
            pass

    # Include live weather for farming/weather queries
    if _is_farming_query(query):
        try:
            parts.append(weather_to_text(get_weather(lat, lon)))
        except Exception:
            pass
        try:
            parts.append(prices_to_text(get_mandi_prices()[:6]))
        except Exception:
            pass

    # Web search for all queries (general knowledge enrichment)
    web = web_search_context(query)
    if web:
        parts.append(web)

    return "\n\n---\n\n".join(parts) if parts else "No additional context available."


# ─────────────────────────────────────────────────────────────
# Track whether Watsonx returned a 403 (project membership issue)
# ─────────────────────────────────────────────────────────────
_watsonx_403 = False  # set to True when a 403 is detected

# ─────────────────────────────────────────────────────────────
# General-purpose smart fallback (no IBM credentials / 403)
# ─────────────────────────────────────────────────────────────
def _smart_fallback(message: str) -> str:
    """Rich, general-purpose fallback that handles any topic."""
    p = message.lower()

    # Organic input preparation (Jeevamrut, Beejamrut, Panchagavya, etc.)
    if any(w in p for w in ["jeevamrut","beejamrut","panchagavya","dashparni",
                              "agniastra","brahmastra","amrit pani","sasyagavya",
                              "prepare","preparation","how to make","how do i prepare",
                              "nske","neem seed kernel","fish amino","fpj","fermented plant",
                              "lab serum","lactic acid","wood vinegar","wca","eggshell",
                              "vermicompost","compost tea","vermi-wash","weed tea"]):
        store = get_vector_store()
        if store:
            try:
                from rag.knowledge_base import retrieve_context
                chunks = retrieve_context(message, store, k=4)
                if chunks and "No relevant" not in chunks:
                    return (f"## 🌿 Organic Input Preparation\n\n"
                            f"{chunks}\n\n"
                            f"[Source: Organic Input Preparation DB]")
            except Exception:
                pass
        return ("## 🌿 Organic Input Preparation\n\n"
                "**Common preparations:**\n\n"
                "| Input | Key Ingredients | Fermentation | Use |\n|---|---|---|---|\n"
                "| **Jeevamrut** | 10 kg cow dung, 10 L urine, 2 kg jaggery, 2 kg besan | 48 hrs | 200 L/acre soil drench |\n"
                "| **Beejamrut** | 5 kg cow dung, 5 L urine, 50 g lime | 12 hrs settle | Seed soak 20–30 min |\n"
                "| **Panchagavya** | Dung, urine, milk, curd, ghee + coconut water | 22 days | 3% foliar spray |\n"
                "| **NSKE 5%** | 5 kg neem kernels / 100 L water | 12 hrs soak | Spray same day |\n"
                "| **Dashparni Ark** | 10 types of leaves + chilli + garlic + urine | 30 days | 3–5% spray |\n\n"
                "Ask me for any specific recipe by name for the full step-by-step instructions!")

    # Math
    if any(w in p for w in ["calculate","compute","solve","math","equation",
                              "integral","derivative","prime","factorial","=","+"]):
        try:
            # Try safe eval for simple arithmetic
            expr = re.sub(r'[^0-9+\-*/.() ]', '', message)
            if expr.strip():
                result = eval(compile(expr, '<string>', 'eval'), {"__builtins__": {}})
                return (f"**Calculation Result**\n\n`{expr.strip()} = {result}`")
        except Exception:
            pass
        return ("**Math Assistant**\n\nI can help with calculations and equations. "
                "Please type your math expression or problem and I'll solve it step by step.")

    # Code
    if any(w in p for w in ["code","python","javascript","function","class","bug","error",
                              "program","algorithm","html","css","sql","api","debug"]):
        return ("**Code Assistant** 💻\n\n"
                "I can write and explain code in Python, JavaScript, HTML/CSS, SQL, and more. "
                "Please describe what you need and I'll write the code for you!")

    # Weather
    if any(w in p for w in ["weather","temperature","rain","humidity","forecast","मौसम","बारिश"]):
        try:
            lat = float(os.getenv("DEFAULT_LAT", 20.59))
            lon = float(os.getenv("DEFAULT_LON", 78.96))
            w   = get_weather(lat, lon)
            return (f"## 🌤️ Current Weather\n\n"
                    f"| Parameter | Value |\n|---|---|\n"
                    f"| Temperature | **{w['temperature']}°C** (feels {w['feels_like']}°C) |\n"
                    f"| Condition | {w['weather_icon']} {w['weather_desc']} |\n"
                    f"| Humidity | {w['humidity']}% |\n"
                    f"| Wind Speed | {w['wind_speed']} km/h |\n"
                    f"| Rainfall Today | {w['precipitation']} mm |\n"
                    f"| Soil Temperature | {w['soil_temp']}°C |\n"
                    f"| Soil Moisture | {w['soil_moisture']}% |\n\n"
                    f"*Updated: {w['updated_at']}* [Source: Open-Meteo]")
        except Exception:
            pass

    # Mandi prices
    if any(w in p for w in ["price","mandi","rate","bhav","market","दाम","भाव","बाजार"]):
        prices = get_mandi_prices()
        rows   = "\n".join(f"| {x['crop']} | ₹{x['modal_price']} | {x['trend']} | {x['mandi']} |"
                           for x in prices[:10])
        return (f"## 📊 Today's Mandi Prices\n\n"
                f"| Crop | Modal (₹/Qtl) | Trend | Mandi |\n|---|---|---|---|\n"
                f"{rows}\n\n"
                f"*Prices as of today. For MSP info: [agmarknet.gov.in](https://agmarknet.gov.in)*\n"
                f"[Source: Mandi DB]")

    # Pest / Disease
    if any(w in p for w in ["pest","disease","insect","virus","fungal","blight","worm","कीट","रोग"]):
        return ("## 🐛 Pest & Disease Management\n\n"
                "**Active Alerts This Season:**\n\n"
                "| Pest/Disease | Crop | Risk | Control |\n|---|---|---|---|\n"
                "| Fall Armyworm | Maize | 🔴 High | Spinetoram 11.7% SC @ 0.5 ml/L |\n"
                "| Leaf Curl Virus | Tomato | 🔴 High | Yellow traps + neem oil 3% |\n"
                "| Rice Blast | Rice | 🔴 High | Tricyclazole 75% WP @ 0.6 g/L |\n"
                "| Cotton Bollworm | Cotton | 🟠 Medium | Emamectin 5% SG + pheromone traps |\n"
                "| Aphids | Mustard | 🟢 Low | Dimethoate 30 EC @ 1 ml/L |\n\n"
                "Always consult your local KVK for confirmed diagnosis. [Source: ICAR Pest DB]")

    # Schemes
    if any(w in p for w in ["scheme","yojana","pm kisan","pmfby","kcc","subsidy","insurance","योजना","बीमा"]):
        return ("## 🏛️ Government Schemes for Farmers\n\n"
                "| Scheme | Benefit | How to Apply |\n|---|---|---|\n"
                "| **PM-KISAN** | ₹6,000/year (3 installments) | pmkisan.gov.in |\n"
                "| **PMFBY** (Crop Insurance) | 2% Kharif / 1.5% Rabi premium | Nearest bank |\n"
                "| **Kisan Credit Card** | ₹3L @ 7% interest | Any co-op/commercial bank |\n"
                "| **PMKSY** (Irrigation) | Drip/sprinkler subsidy 55% | District agriculture office |\n"
                "| **eNAM** | Online mandi access | enam.gov.in |\n\n"
                "[Source: Govt Schemes DB]")

    # Crops
    if any(w in p for w in ["crop","sow","plant","harvest","seed","kharif","rabi","season","खेती","फसल"]):
        season = get_season()
        recs   = recommend_crops("Loamy", season)
        crops  = "**, **".join(recs["recommended_crops"])
        tips   = "\n".join(f"{i+1}. {t}" for i, t in enumerate(recs["tips"]))
        return (f"## 🌱 Crop Recommendations ({season} Season)\n\n"
                f"**Best crops for Loamy soil:** **{crops}**\n\n"
                f"**Agronomic Tips:**\n{tips}\n\n"
                f"[Source: Crop Calendar DB]")

    # General fallback — no LLM credentials configured at all
    return ("## 👋 Hi, I'm Kisan Mitra!\n\n"
            "I'm a general-purpose AI assistant with deep farming expertise. I can help with:\n\n"
            "**🌾 Agriculture**\n"
            "- Crop selection, sowing schedules, soil management\n"
            "- Pest & disease identification and treatment\n"
            "- Live weather and irrigation advice\n"
            "- Mandi prices for 12+ crops\n"
            "- Government schemes (PM-Kisan, PMFBY, KCC)\n\n"
            "**🧠 General Knowledge**\n"
            "- Science, history, geography, math\n"
            "- Coding in Python, JS, HTML, SQL and more\n"
            "- Translation between Indian and world languages\n"
            "- Creative writing, summaries, analysis\n\n"
            "**To enable AI responses, add one free API key to your `.env` file:**\n\n"
            "| Provider | Get Free Key | .env variable |\n|---|---|---|\n"
            "| **Groq** (Llama 3.3 70B) | [console.groq.com](https://console.groq.com) | `GROQ_API_KEY=...` |\n"
            "| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com) | `GEMINI_API_KEY=...` |\n\n"
            "Ask me anything! 🚀")


def _extract_sources(text: str) -> list:
    return re.findall(r'\[Source:\s*([^\]]+)\]', text)


# ─────────────────────────────────────────────────────────────
# Page Routes
# ─────────────────────────────────────────────────────────────
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/chat")
def chat_page():
    return render_template("chat.html")

@app.route("/diseases")
def diseases_page():
    return render_template("diseases.html")

@app.route("/rates")
def rates_page():
    return render_template("rates.html")

@app.route("/home")
def index():
    return render_template("dashboard.html")


# ─────────────────────────────────────────────────────────────
# API: JSON chat (used by dashboard + non-streaming)
# ─────────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data      = request.get_json(force=True)
    message   = (data.get("message") or "").strip()
    language  = data.get("language", "en")
    lat       = float(data.get("lat", os.getenv("DEFAULT_LAT", 20.59)))
    lon       = float(data.get("lon", os.getenv("DEFAULT_LON", 78.96)))
    voice_out = data.get("voice_out", False)

    if not message:
        return jsonify({"error": "Empty message"}), 400

    history = session.get("chat_history", [])
    history_text = "\n".join(
        f"User: {h['q']}\nAssistant: {h['a']}" for h in history[-5:]
    )
    context = build_context(message, lat, lon)
    prompt  = SYSTEM_PROMPT.format(
        context=context,
        history=history_text or "None",
        question=message,
    )

    # Build messages for Groq / Gemini
    msgs = _build_messages(context, history_text, message)

    # Try Groq → Gemini → IBM SDK → IBM REST → fallback
    answer = None

    if not answer and _has_groq():
        answer = call_groq(msgs)

    if not answer and _has_gemini():
        answer = call_gemini(msgs)

    if not answer:
        model = get_watsonx_model()
        if model:
            try:
                answer = model.generate_text(prompt=prompt)
                if answer and len(answer.strip()) > 5:
                    answer = answer.strip()
                else:
                    answer = None
            except Exception as e:
                logger.error(f"SDK error: {e}")

    if not answer:
        answer = call_watsonx_rest(prompt)

    if not answer:
        answer = _smart_fallback(message)

    history.append({"q": message, "a": answer})
    session["chat_history"] = history[-20:]

    audio_url = None
    if voice_out:
        audio_url = text_to_speech(answer, language=language)

    def _active_model_name() -> str:
        if _has_groq():
            return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if _has_gemini():
            return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if has_ibm_credentials():
            return os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2")
        return "Kisan Mitra AI"

    return jsonify({
        "answer":    answer,
        "audio_url": audio_url,
        "sources":   _extract_sources(answer),
        "model":     _active_model_name(),
        "powered_by": (
            "Groq · Llama 3.3 70B" if _has_groq() else
            "Google Gemini 1.5 Flash" if _has_gemini() else
            "IBM Watsonx Granite" if has_ibm_credentials() else
            "Kisan Mitra AI"
        ),
    })


# ─────────────────────────────────────────────────────────────
# API: SSE streaming chat  (used by /chat page)
# ─────────────────────────────────────────────────────────────
@app.route("/api/chat/stream", methods=["POST"])
def api_chat_stream():
    """Server-Sent Events streaming endpoint for the chat page."""
    data     = request.get_json(force=True)
    message  = (data.get("message") or "").strip()
    lat      = float(data.get("lat", os.getenv("DEFAULT_LAT", 20.59)))
    lon      = float(data.get("lon", os.getenv("DEFAULT_LON", 78.96)))

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Read session state BEFORE entering the generator (Flask session is
    # request-scoped and cannot be reliably written inside a generator).
    history      = list(session.get("chat_history", []))
    history_text = "\n".join(
        f"User: {h['q']}\nAssistant: {h['a']}" for h in history[-5:]
    )
    context = build_context(message, lat, lon)
    prompt  = SYSTEM_PROMPT.format(
        context=context,
        history=history_text or "None",
        question=message,
    )
    msgs = _build_messages(context, history_text, message)

    def event_stream():
        full_answer = []

        # 1a. Try Groq streaming (fastest free LLM)
        if not full_answer and _has_groq():
            try:
                for chunk in stream_groq(msgs):
                    full_answer.append(chunk)
                    yield f"data: {json.dumps({'token': chunk})}\n\n"
            except Exception as e:
                logger.error(f"Groq stream error: {e}")
                full_answer = []   # reset so next provider is tried

        # 1b. Try Gemini streaming
        if not full_answer and _has_gemini():
            try:
                for chunk in stream_gemini(msgs):
                    full_answer.append(chunk)
                    yield f"data: {json.dumps({'token': chunk})}\n\n"
            except Exception as e:
                logger.error(f"Gemini stream error: {e}")
                full_answer = []

        # 1c. Try Watsonx streaming
        if not full_answer and has_ibm_credentials():
            try:
                for chunk in stream_watsonx_rest(prompt):
                    full_answer.append(chunk)
                    yield f"data: {json.dumps({'token': chunk})}\n\n"
            except Exception as e:
                logger.error(f"Watsonx stream error: {e}")
                full_answer = []

        # 2. If all streaming attempts gave nothing, fall back to non-streaming
        if not full_answer:
            answer = None

            if _has_groq():
                answer = call_groq(msgs)
            if not answer and _has_gemini():
                answer = call_gemini(msgs)
            if not answer:
                wx_model = get_watsonx_model()
                if wx_model:
                    try:
                        answer = wx_model.generate_text(prompt=prompt)
                        if answer:
                            answer = answer.strip()
                    except Exception:
                        pass
            if not answer:
                answer = call_watsonx_rest(prompt)
            if not answer:
                answer = _smart_fallback(message)

            # Simulate streaming by word-chunking the fallback answer
            full_answer = [answer]
            CHUNK = 8
            for i in range(0, len(answer), CHUNK):
                piece = answer[i:i + CHUNK]
                yield f"data: {json.dumps({'token': piece})}\n\n"
                time.sleep(0.008)

        # 3. Persist history via a follow-up request-context push
        final = "".join(full_answer)
        history.append({"q": message, "a": final})
        # Push context so session writes work inside stream_with_context
        with app.app_context():
            pass  # context already active; session saved after Response completes
        # Store on the session object directly — it is flushed when the
        # response finishes because we use stream_with_context.
        session["chat_history"] = history[-20:]
        session.modified = True

        # 4. Done event with metadata
        active_model = (
            os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile") if _has_groq() else
            os.getenv("GEMINI_MODEL", "gemini-1.5-flash")       if _has_gemini() else
            os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2") if has_ibm_credentials() else
            "Kisan Mitra AI"
        )
        yield f"data: {json.dumps({'done': True, 'sources': _extract_sources(final), 'model': active_model})}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─────────────────────────────────────────────────────────────
# Other API routes
# ─────────────────────────────────────────────────────────────
@app.route("/api/weather", methods=["GET"])
def api_weather():
    lat = float(request.args.get("lat", os.getenv("DEFAULT_LAT", 20.59)))
    lon = float(request.args.get("lon", os.getenv("DEFAULT_LON", 78.96)))
    return jsonify(get_weather(lat, lon))

@app.route("/api/mandi", methods=["GET"])
def api_mandi():
    crops_param = request.args.get("crops","")
    crops = [c.strip() for c in crops_param.split(",") if c.strip()] if crops_param else None
    return jsonify(get_mandi_prices(crops))

@app.route("/api/crops", methods=["GET"])
def api_crops():
    return jsonify(recommend_crops(request.args.get("soil","Loamy"), request.args.get("season",None)))

@app.route("/api/voice", methods=["POST"])
def api_voice():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400
    audio_file = request.files["audio"]
    language   = request.form.get("language","hi")
    tmp_path   = f"static/audio/tmp_{os.urandom(4).hex()}.wav"
    audio_file.save(tmp_path)
    transcript = speech_to_text(tmp_path, language=language)
    try: os.remove(tmp_path)
    except OSError: pass
    return jsonify({"transcript": transcript})

@app.route("/api/clear_history", methods=["POST"])
def api_clear():
    session.pop("chat_history", None)
    return jsonify({"status": "cleared"})

@app.route("/api/diseases", methods=["GET"])
def api_diseases():
    from services.diseases import DISEASE_DB
    crop_filter = request.args.get("crop","").strip().lower()
    data = DISEASE_DB if not crop_filter else [
        d for d in DISEASE_DB if crop_filter in d["crop"].lower()
    ]
    return jsonify(data)

@app.route("/static/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory("static/audio", filename)

@app.route("/api/status", methods=["GET"])
def api_status():
    active = (
        "groq"   if _has_groq()   else
        "gemini" if _has_gemini() else
        "ibm"    if has_ibm_credentials() else
        "fallback"
    )
    model = (
        os.getenv("GROQ_MODEL",       "llama-3.3-70b-versatile") if _has_groq()   else
        os.getenv("GEMINI_MODEL",     "gemini-1.5-flash")         if _has_gemini() else
        os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2")  if has_ibm_credentials() else
        "Kisan Mitra AI"
    )
    return jsonify({
        "ibm_configured":    has_ibm_credentials(),
        "groq_configured":   _has_groq(),
        "gemini_configured": _has_gemini(),
        "active_provider":   active,
        "model":             model,
        "streaming":         True,
    })


if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG","true").lower() == "true"

    # ── Startup provider banner ─────────────────────────────
    if _has_groq():
        active = f"Groq  ({os.getenv('GROQ_MODEL','llama-3.3-70b-versatile')})"
    elif _has_gemini():
        active = f"Gemini  ({os.getenv('GEMINI_MODEL','gemini-1.5-flash')})"
    elif has_ibm_credentials():
        active = f"IBM Watsonx  ({os.getenv('WATSONX_MODEL_ID','ibm/granite-13b-chat-v2')})"
    else:
        active = "Smart Fallback  (no LLM key configured)"

    logger.info("=" * 54)
    logger.info(f"  Kisan Mitra starting on port {port}")
    logger.info(f"  Active LLM  :  {active}")
    logger.info(f"  Groq         :  {'YES  key=' + os.getenv('GROQ_API_KEY','')[:12] if _has_groq() else 'not configured'}")
    logger.info(f"  Gemini       :  {'YES' if _has_gemini() else 'not configured'}")
    logger.info(f"  IBM Watsonx  :  {'YES' if has_ibm_credentials() else 'not configured'}")
    logger.info("=" * 54)

    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
