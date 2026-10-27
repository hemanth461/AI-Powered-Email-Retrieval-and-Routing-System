# ⚡ Autonomous AI Email Retrieval & Department Routing System

<div align="center">

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Render_App-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://ai-powered-email-retrieval-and-routing.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![HuggingFace](https://img.shields.io/badge/Model-BERT%20%2B%20VADER-orange?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

**An enterprise-grade, autonomous NLP pipeline that ingests unread customer emails via Gmail API, performs multi-task intent classification and sentiment urgency triage, maintains a full PostgreSQL audit trail, and automatically routes emails to designated departmental mailboxes.**

[Explore Live Demo](https://ai-powered-email-retrieval-and-routing.onrender.com) • [Report Bug](https://github.com/hemanth461/Autonomous-Email-Retrieval-and-Routing-System/issues) • [Request Feature](https://github.com/hemanth461/Autonomous-Email-Retrieval-and-Routing-System/issues)

</div>

---

> 🚀 **Live Production Deployment**:
> **[https://ai-powered-email-retrieval-and-routing.onrender.com](https://ai-powered-email-retrieval-and-routing.onrender.com)**
> *(Hosted on Render with automatic health-check pingers to ensure 24/7 availability. Note: If the service is idling, initial cold-start may take ~45–60 seconds).*

---

## 📸 Visual Interface & Demo Gallery

### 1. Live AI Playground
Interactive multi-task testing sandbox with real-time intent classification, softmax confidence distribution, VADER sentiment polarity, and priority score computation.

![Live AI Playground](docs/screenshots/01_ai_playground.png)

---

### 2. Gmail Automation & Batch Processing
End-to-end OAuth 2.0 inbox scanner that retrieves unread emails, runs deduplication checks, triggers NLP classification, and automatically dispatches routed copies to target department mailboxes.

![Gmail Automation](docs/screenshots/02_gmail_automation.png)

---

### 3. Executive Analytics & Operational Insights
Real-time KPI metric cards (Total Inbound, Auto-Routed, Critical/High Priority, Processing Latency), departmental workload volume distribution, and priority tier breakdown charts.

![Executive Analytics](docs/screenshots/03_executive_analytics.png)

---

### 4. Inbound Email History & Audit Log
Searchable, filterable PostgreSQL audit ledger displaying historical email records, sender metadata, classified categories, sentiment scores, routed target inboxes, and localized IST timestamps.

![Email History](docs/screenshots/04_email_history.png)

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   Inbound Gmail Mail   │
                                  │  (Customer Inquiries)  │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                 ┌──────────────────────────┐
                                 │    Google Gmail API      │
                                 │   OAuth 2.0 Desktop/App  │
                                 └────────────┬─────────────┘
                                              │
                                              ▼
┌─────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
│   Streamlit Frontend    │◄────►│     FastAPI Backend      │◄────►│  PostgreSQL Audit Store  │
│  • AI Playground        │ REST │  • Async Ingestion Engine│ SQLAlchemy                       │
│  • Inbox Automation     │ JSON │  • Dedup Guard           │      │  • email_records         │
│  • Executive Analytics  │      │  • Background Scheduler  │      │  • Status & Error Logs   │
│  • Audit History Table  │      │  • Auto-Forward Dispatch │      └──────────────────────────┘
└─────────────────────────┘      └────────────┬─────────────┘
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
      ┌──────────────────────────┐                       ┌──────────────────────────┐
      │   Fine-Tuned BERT NLP    │                       │  VADER Sentiment Engine  │
      │ • 8 Intent Categories    │                       │ • Polarity Compound (-1..1)
      │ • Softmax Confidence %   │                       │ • Urgency Keyword Filter │
      │ • Multi-class Logits     │                       │ • Priority Matrix (L/M/H)│
      └─────────────┬────────────┘                       └─────────────┬────────────┘
                    │                                                  │
                    └─────────────────────────┬────────────────────────┘
                                              │
                                              ▼
                                ┌──────────────────────────┐
                                │   Department Dispatch    │
                                └─────────────┬────────────┘
                                              │
        ┌───────────────────┬─────────────────┼───────────────────┬───────────────────┐
        ▼                   ▼                 ▼                   ▼                   ▼
 ┌──────────────┐    ┌──────────────┐  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │  HR Inbox    │    │ Sales Inbox  │  │Billing Inbox │    │   IT Inbox   │    │ Escalations  │
 └──────────────┘    └──────────────┘  └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🎯 Department Routing Matrix

Every inbound inquiry is analyzed, mapped to an organizational department, and dispatched to a dedicated recipient inbox:

| Category | Target Department | Description & Typical Scenarios | Monitored Mailbox |
| :--- | :--- | :--- | :--- |
| **HR & Recruitment** | Human Resources | Job applications, resumes, leave requests, employee inquiries | `hrroutingretrieval@gmail.com` |
| **Sales & Business** | Sales & Growth | Product inquiries, partnership deals, enterprise quotes, demos | `salesroutingretrieval@gmail.com` |
| **Billing & Payments** | Finance & Billing | Invoice disputes, subscription refunds, payment failures | `billingroutingretrieval@gmail.com` |
| **IT & Infrastructure** | IT Support & DevOps | VPN access, server outages, software credentials, bug reports | `itroutingretrieval@gmail.com` |
| **Customer Support** | Customer Support | How-to questions, service feedback, general product guidance | Configurable in `.env` |
| **Legal & Compliance** | Legal & Compliance | GDPR/privacy requests, contract audits, policy terms | Configurable in `.env` |
| **Marketing & PR** | Marketing & PR | Press releases, sponsorship proposals, brand collaborations | Configurable in `.env` |
| **Escalations** | Executive Escalations | High-urgency negative complaints, legal threats, critical risks | Configurable in `.env` |

---

## 🌟 Key Features

- **Autonomous Gmail Pipeline**: Polls unread emails via OAuth 2.0 with automatic token refresh, parses RFC 2822 headers and MIME multi-part bodies, and marks emails read upon successful routing.
- **Deduplication Engine**: Uses the unique Google `message_id` as an idempotent barrier in PostgreSQL to prevent duplicate processing or forwarding loops.
- **Multi-Task NLP Classification**:
  - **Fine-Tuned BERT (`bert-base-uncased`)**: Accurately classifies emails across 8 corporate departments with softmax confidence distributions.
  - **VADER Sentiment & Urgency Analyzer**: Evaluates emotional polarity and urgent keywords (`urgent`, `critical`, `immediate`, `deadline`, `asap`) to generate priority tiers (`LOW`, `MEDIUM`, `HIGH`).
- **Resilient Cloud Persistence**: Backed by PostgreSQL with SQLAlchemy ORM, storing complete message content, attachments metadata, prediction metrics, routing status, and millisecond latency.
- **Fail-Safe Routing**: If network errors occur during forwarding, the record is marked as `failed` with the exact error message preserved, enabling one-click manual re-dispatch from the UI.
- **Ephemeral-Safe OAuth Caching**: Seamlessly stores refreshed tokens in `/tmp/` across containerized cloud restarts on Render.
- **Clean Executive Dashboard**: Built with Streamlit, Plotly, and Altair, featuring interactive filters, metric cards, and charts in localized Indian Standard Time (IST).

---

## 🛠️ Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Backend & Microservices** | FastAPI, Uvicorn, Pydantic v2, APScheduler, Python 3.10+ |
| **Machine Learning & NLP** | PyTorch, Hugging Face Transformers (BERT), NLTK VADER, Scikit-Learn |
| **Frontend & Analytics** | Streamlit, Plotly Express, Altair, HTML5/CSS3 custom badges |
| **Database & ORM** | PostgreSQL, SQLAlchemy 2.0, Psycopg2-binary |
| **Google Cloud APIs** | Google Gmail API v1, Google Auth OAuthlib, Google API Python Client |
| **Cloud Infrastructure** | Render (Docker & Web Services), UptimeRobot (Uptime Monitoring) |

---

## 📁 Repository Structure

```
Autonomous-AI-Email-Retrieval-and-Routing-System/
├── frontend/
│   └── app.py                     # Streamlit frontend with 4 specialized tabs & dark UI
├── backend/
│   ├── main.py                    # FastAPI entrypoint, CORS middleware & poller
│   ├── schemas.py                 # Pydantic request/response validation schemas
│   ├── routers/
│   │   ├── emails.py              # GET /emails, POST /emails/fetch, GET /emails/{id}
│   │   ├── classification.py      # POST /classify (real-time test sandbox)
│   │   ├── routing.py             # POST /route/{id} (manual routing trigger)
│   │   └── dashboard.py           # GET /dashboard/stats (KPI metrics & distributions)
│   └── services/
│       ├── gmail_service.py       # Gmail OAuth 2.0, fetching, formatting & sending
│       ├── classifier_service.py  # BERT inference + VADER priority engine
│       └── routing_service.py     # End-to-end pipeline orchestration
├── ml_model/
│   ├── bert_classifier.py         # PyTorch BERT model loader and tokenizer
│   └── sentiment_analyzer.py      # VADER sentiment and urgency scoring logic
├── database/
│   ├── models.py                  # SQLAlchemy ORM model: EmailRecord
│   ├── db.py                      # Database engine & scoped session lifecycle
│   └── crud.py                    # Database queries, pagination, deduplication
├── config/
│   ├── settings.py                # Environment configuration via Pydantic BaseSettings
│   └── department_mapping.py      # Category-to-Department and routing email mapping
├── docs/
│   └── screenshots/               # Production UI screenshots for documentation
├── scripts/
│   ├── generate_email_data.py     # Generates synthetic domain email dataset
│   ├── train_bert.py              # Fine-tunes BERT model on dataset
│   ├── evaluate_models.py         # Evaluates accuracy, F1-score & latency
│   └── init_db.py                 # Initializes PostgreSQL database schema
├── credentials/                   # OAuth credentials (gitignored for security)
├── render.yaml                    # Infrastructure-as-code for Render deployment
├── requirements.txt               # Production Python dependencies
└── README.md                      # Project documentation
```

---

## 🚀 Getting Started Locally

### 1. Prerequisites
- Python 3.10 or 3.11
- PostgreSQL installed and running locally (or a cloud PostgreSQL URI)
- Google Cloud Console project with Gmail API enabled

### 2. Clone Repository
```bash
git clone https://github.com/hemanth461/Autonomous-Email-Retrieval-and-Routing-System.git
cd Autonomous-Email-Retrieval-and-Routing-System
```

### 3. Create Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/email_triage

# Gmail OAuth
GMAIL_CREDENTIALS_FILE=credentials/gmail_credentials.json
GMAIL_TOKEN_FILE=credentials/gmail_token.json
GMAIL_MONITORED_ACCOUNT=your-monitored-inbox@gmail.com

# Department Target Mailboxes
DEPT_HR_EMAIL=hrroutingretrieval@gmail.com
DEPT_SALES_EMAIL=salesroutingretrieval@gmail.com
DEPT_BILLING_EMAIL=billingroutingretrieval@gmail.com
DEPT_IT_EMAIL=itroutingretrieval@gmail.com
DEPT_SUPPORT_EMAIL=support@yourcompany.com
DEPT_LEGAL_EMAIL=legal@yourcompany.com
DEPT_MARKETING_EMAIL=marketing@yourcompany.com
DEPT_ESCALATION_EMAIL=escalations@yourcompany.com

# Background Polling
POLL_INTERVAL_SECONDS=60
BACKEND_URL=http://localhost:8000
```

### 6. Initialize PostgreSQL Database
```bash
python scripts/init_db.py
```

### 7. Setup Google Cloud Gmail OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API** under **APIs & Services**.
3. Create an **OAuth 2.0 Client ID** (Application type: *Desktop App*).
4. Download the JSON file and save it as `credentials/gmail_credentials.json`.
5. On the first run, a browser window will open requesting consent. Once approved, `gmail_token.json` is generated automatically.

### 8. Train or Download BERT Weights
```bash
# Generate synthetic corporate emails:
python scripts/generate_email_data.py

# Fine-tune BERT classifier:
python scripts/train_bert.py
```

### 9. Launch Backend & Frontend

**Terminal 1 (FastAPI Backend):**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Streamlit UI):**
```bash
streamlit run frontend/app.py
```

- **Streamlit Interface:** `http://localhost:8501`
- **FastAPI Interactive Docs (Swagger UI):** `http://localhost:8000/docs`

---

## 🌐 Cloud Deployment (Render)

This repository includes a turnkey `render.yaml` blueprint for one-click deployment:

1. Connect your GitHub repository to [Render](https://render.com/).
2. Add a **PostgreSQL** instance on Render and copy the internal `DATABASE_URL`.
3. Add a **Web Service** with:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `sh -c "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0"`
4. Add environment variables:
   - `DATABASE_URL`: Your Render PostgreSQL connection string.
   - `BACKEND_URL`: `http://localhost:8000`
   - `GMAIL_CREDENTIALS_JSON`: Stringified JSON of `gmail_credentials.json`.
   - `GMAIL_TOKEN_JSON`: Stringified JSON of `gmail_token.json`.
5. *(Optional)* Setup a free 5-minute ping monitor on [UptimeRobot](https://uptimerobot.com/) targeting your URL to prevent Render free-tier cold sleep.

---

## 📊 Database Schema (`email_records`)

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` | Primary key identifier |
| `gmail_message_id` | `VARCHAR` | Unique Gmail message identifier (prevents duplicate triage) |
| `thread_id` | `VARCHAR` | Gmail conversation thread identifier |
| `sender` | `VARCHAR` | Sender email address and name |
| `receiver` | `VARCHAR` | Inbound receiver address |
| `subject` | `TEXT` | Extracted email subject line |
| `body` | `TEXT` | Extracted email body text |
| `has_attachments` | `BOOLEAN` | Attachment flag |
| `attachment_names` | `TEXT` | Comma-delimited list of attached filenames |
| `received_at` | `TIMESTAMP` | RFC 2822 email timestamp |
| `predicted_category` | `VARCHAR` | Raw ML classification label |
| `predicted_department` | `VARCHAR` | Canonical department name |
| `department_email` | `VARCHAR` | Destination inbox email |
| `confidence` | `FLOAT` | Softmax probability score (0.0 to 1.0) |
| `sentiment_label` | `VARCHAR` | `POSITIVE`, `NEUTRAL`, or `NEGATIVE` |
| `sentiment_score` | `FLOAT` | VADER compound sentiment score (-1.0 to +1.0) |
| `urgency_level` | `VARCHAR` | `low`, `medium`, `high`, `critical` |
| `priority` | `VARCHAR` | `LOW`, `MEDIUM`, `HIGH` |
| `routing_status` | `VARCHAR` | `pending`, `routed`, `failed` |
| `routed_at` | `TIMESTAMP` | Timestamp of automated dispatch |
| `routing_error` | `TEXT` | Captured error traceback if dispatch fails |
| `processed_at` | `TIMESTAMP` | Timestamp of classification completion |
| `processing_time_ms` | `INTEGER` | Pipeline execution latency in milliseconds |

---

## 🔒 Security & Privacy

- **OAuth 2.0 Authentication**: No email passwords or app passwords are stored. Access tokens use Google's scoped permissions (`gmail.readonly`, `gmail.modify`, `gmail.send`).
- **Secret Isolation**: All credentials, tokens, and database passwords are kept in `.env` and `.gitignore`.
- **Stateless Cloud Tokens**: Production uses environment-based JSON tokens cached in ephemeral `/tmp/` storage, preventing unauthorized access.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👤 Author

**Hemanth Kumar K**
- GitHub: [@hemanth461](https://github.com/hemanth461)
- Live Project: [Autonomous AI Email Routing System](https://ai-powered-email-retrieval-and-routing.onrender.com)
