# Kisan Mitra – Deployment Guide
## IBM Cloud Foundry + GitHub Pages

---

## 1. Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| pip | 24+ |
| git | any |
| IBM Cloud CLI | 2.x (`ibmcloud`) |
| Cloud Foundry plugin | `cf` |

```bash
# Install IBM Cloud CLI (Windows PowerShell)
winget install IBM.IBMCloudCLI

# Install CF plugin
ibmcloud cf install
```

---

## 2. Local Development Setup

```bash
# 1. Clone repo
git clone https://github.com/<you>/kisan-mitra.git
cd kisan-mitra

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux

# 5. Edit .env with your IBM credentials:
#    IBM_API_KEY=...
#    IBM_PROJECT_ID=...
#    FLASK_SECRET_KEY=<random string>

# 6. Run the app
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
# Open http://localhost:5000
```

---

## 3. Get IBM Watsonx.ai Credentials (Free Tier)

1. Sign up at https://cloud.ibm.com (Lite account — free)
2. Create a **Watson Machine Learning** service instance
3. Go to **Manage > Access (IAM)** → Create an **API key** → copy to `.env`
4. Open **Watsonx.ai** → Create a **project** → copy the **Project ID** to `.env`
5. Supported model on Lite: `ibm/granite-13b-chat-v2`

> **Lite tier limits**: ~50,000 tokens/month free. Sufficient for testing.

---

## 4. Deploy to IBM Cloud Foundry

```bash
# Log in
ibmcloud login -a https://cloud.ibm.com --sso
ibmcloud target -r us-south -o <your_org> -s <your_space>

# Push the app (manifest.yml is used automatically)
ibmcloud cf push

# Set environment variables (instead of .env on Cloud)
ibmcloud cf set-env kisan-mitra IBM_API_KEY        "your_key"
ibmcloud cf set-env kisan-mitra IBM_PROJECT_ID     "your_project_id"
ibmcloud cf set-env kisan-mitra FLASK_SECRET_KEY   "random_secret"
ibmcloud cf restage kisan-mitra

# View logs
ibmcloud cf logs kisan-mitra --recent
```

App URL: `https://kisan-mitra-<random>.mybluemix.net`

---

## 5. manifest.yml (already included)

```yaml
applications:
  - name: kisan-mitra
    memory: 512M
    instances: 1
    buildpacks:
      - python_buildpack
    command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
    env:
      FLASK_ENV: production
```

---

## 6. GitHub Pages (Static Preview)

The frontend can be exported as a static demo page:

```bash
# Build static snapshot (optional – for GitHub Pages demo)
# The full dynamic app requires Python/Flask and cannot run on GH Pages.
# Host the API on IBM Cloud and point the frontend's fetch() calls
# to the IBM Cloud URL by updating BASE_URL in static/js/app.js.
```

To host the demo:
1. Push the repo to GitHub
2. Go to **Settings → Pages → Source: main / root**
3. The `index.html` in the root (if present) would be served statically.

For a fully functional deployment, use **IBM Cloud Foundry** (Step 4).

---

## 7. Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `IBM_API_KEY` | ✅ | IBM Cloud IAM API Key |
| `IBM_PROJECT_ID` | ✅ | Watsonx.ai Project ID |
| `IBM_WATSONX_URL` | ❌ | Default: `https://us-south.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | ❌ | Default: `ibm/granite-13b-chat-v2` |
| `FLASK_SECRET_KEY` | ✅ | Random secret for sessions |
| `DEFAULT_LAT` | ❌ | Default farm latitude (India centre) |
| `DEFAULT_LON` | ❌ | Default farm longitude |
| `PORT` | ❌ | HTTP port (Cloud sets automatically) |

---

## 8. FAISS Index Rebuild

If you update the knowledge base (`rag/knowledge_base.py`), force a rebuild:

```bash
python -c "from rag.knowledge_base import load_vector_store; load_vector_store(force_rebuild=True)"
```

---

## 9. Troubleshooting

| Issue | Fix |
|-------|-----|
| `ImportError: faiss` | `pip install faiss-cpu` |
| `sentence_transformers` slow first run | It downloads the model once (~90 MB) |
| Watsonx 401 Unauthorized | Check `IBM_API_KEY` and `IBM_PROJECT_ID` |
| Voice input not working | Browser needs HTTPS for `getUserMedia` |
| Port already in use | `set PORT=5001` or change in `.env` |
