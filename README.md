# 📧 AI Email Classification & Automatic Department Routing System

A production-oriented extension of the original Streamlit + BERT + VADER
email triage demo. It now retrieves real unread mail from Gmail, classifies
and prioritizes it, stores a full audit trail in PostgreSQL, and
automatically forwards each email to the right department mailbox — all
through a FastAPI backend, with Streamlit as a thin REST client.

---

## 1. Architecture

```
┌─────────────┐        REST (JSON)       ┌───────────────────┐
│  Streamlit   │  ───────────────────►   │   FastAPI Backend  │
│  Frontend    │  ◄───────────────────   │                    │
└─────────────┘                          └─────────┬──────────┘
                                                     │
                     ┌───────────────────────────────┼───────────────────────────┐
                     │                               │                           │
                     ▼                               ▼                           ▼
             ┌──────────────┐               ┌────────────────┐         ┌─────────────────┐
             │  Gmail API    │               │   ML Pipeline   │         │   PostgreSQL     │
             │ (fetch/send)  │               │ BERT + VADER    │         │  (audit trail)   │
             └──────────────┘               └────────────────┘         └─────────────────┘
```

Flow for one email:

1. **Fetch** — `GmailService` pulls unread messages (sender, receiver,
   subject, body, timestamp, attachment names) via the Gmail API.
2. **Dedup check** — the Gmail `message_id` is checked against
   `email_records` before any processing happens, so nothing is classified
   or routed twice.
3. **Classify** — the existing fine-tuned BERT model predicts a category
   (sales / support / billing / hr / it / legal / complaint / general);
   VADER scores sentiment and urgency keywords; these combine into a
   priority (low/medium/high).
4. **Map to department** — category → department name + mailbox address
   (`config/department_mapping.py`, addresses configurable via `.env`).
5. **Persist** — a full row is written to PostgreSQL (`email_records`).
6. **Route** — the email is forwarded via the Gmail API to the department
   mailbox; the row's `routing_status` becomes `routed` or `failed`
   (with the error captured for retry).
7. **Mark read** — the original Gmail message is marked read so it isn't
   re-fetched.

A background APScheduler job repeats steps 1–7 every
`POLL_INTERVAL_SECONDS` (default 60s) once Gmail credentials are present.
You can also trigger it on demand from the Streamlit "Gmail Inbox" tab or
via `POST /emails/fetch`.

---

## 2. Project Structure

```
email_triage_v2/
├── frontend/
│   └── app.py                  # Streamlit UI - calls the backend over REST only
├── backend/
│   ├── main.py                 # FastAPI app, CORS, startup, background poller
│   ├── schemas.py              # Pydantic request/response models
│   ├── routers/
│   │   ├── emails.py           # POST /emails/fetch, GET /emails, GET /emails/{id}
│   │   ├── classification.py   # POST /classify (ad-hoc, no Gmail/DB)
│   │   ├── routing.py          # POST /route/{id} (manual re-route)
│   │   └── dashboard.py        # GET /dashboard/stats
│   └── services/
│       ├── gmail_service.py    # OAuth, fetch unread, forward, mark read
│       ├── classifier_service.py  # BERT + VADER + department resolution
│       └── routing_service.py  # Orchestrates fetch -> classify -> store -> route
├── ml_model/
│   ├── bert_classifier.py      # BERT inference (unchanged from original system)
│   └── sentiment_analyzer.py   # VADER sentiment + urgency + priority scoring
├── database/
│   ├── models.py                # SQLAlchemy ORM: EmailRecord
│   ├── db.py                    # Engine/session management, init_db()
│   └── crud.py                  # Queries: dedup check, list/search, dashboard stats
├── config/
│   ├── settings.py              # pydantic-settings, loads .env
│   └── department_mapping.py    # category -> {department name, routing email}
├── scripts/
│   ├── generate_email_data.py   # Synthetic training data generator
│   ├── train_bert.py            # Fine-tunes bert-base-uncased on the data
│   ├── evaluate_models.py       # Accuracy/latency benchmarking
│   └── init_db.py               # One-off: create PostgreSQL tables
├── credentials/                 # gmail_credentials.json / gmail_token.json (gitignored)
├── data/                        # Generated training CSVs (gitignored)
├── models/bert/                 # Fine-tuned model weights (gitignored)
├── logs/                        # app.log
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 3. Setup

### 3.1 Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 PostgreSQL

```bash
# create the database (adjust user/password as needed)
createdb email_triage

cp .env.example .env
# edit .env -> set DATABASE_URL to match your Postgres instance

python scripts/init_db.py       # creates the email_records table
```

### 3.3 Gmail API / OAuth

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project and enable the **Gmail API**.
2. Under **APIs & Services → Credentials**, create an **OAuth Client ID**
   of type **Desktop App**.
3. Download the resulting JSON and save it as
   `credentials/gmail_credentials.json`.
4. Set `GMAIL_MONITORED_ACCOUNT` in `.env` to the mailbox you want to
   monitor.
5. The first time the backend calls the Gmail API (either via the
   scheduler or `POST /emails/fetch`), a browser window opens for you to
   grant consent. The resulting token is cached to
   `credentials/gmail_token.json` so future runs are non-interactive.

Scopes requested: `gmail.readonly`, `gmail.modify` (mark as read),
`gmail.send` (forward to departments).

### 3.4 Department routing addresses

Edit the `DEPT_*_EMAIL` values in `.env` to point at your real department
mailboxes (see `.env.example`).

### 3.5 Train the BERT classifier

The classification model is not included (weights are large and
environment-specific) — train it locally:

```bash
python scripts/generate_email_data.py     # -> data/email_training_data.csv
python scripts/train_bert.py              # fine-tunes bert-base-uncased, ~few min on GPU
```

This produces `models/bert/fine_tuned_model/`, `models/bert/tokenizer/`,
and `models/bert/label_encoder.joblib`, which `ml_model/bert_classifier.py`
loads automatically.

### 3.6 Run the system

```bash
# Terminal 1: backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: frontend
streamlit run frontend/app.py
```

- Backend docs (Swagger UI): http://localhost:8000/docs
- Frontend dashboard: http://localhost:8501

---

## 4. API Reference

| Method | Endpoint            | Description |
|--------|----------------------|-------------|
| GET    | `/health`             | Liveness check |
| POST   | `/emails/fetch`       | Pull unread Gmail, classify, store, route. Query param `max_results` (default 20). |
| GET    | `/emails`             | List/search stored emails. Query params: `department`, `priority`, `routing_status`, `search`, `limit`, `offset`. |
| GET    | `/emails/{id}`        | Fetch a single stored email record. |
| POST   | `/classify`            | Classify raw `{subject, body}` text without touching Gmail/DB — used by the Manual Classification tab. |
| POST   | `/route/{id}`          | (Re)forward a stored email to its department mailbox — used to retry failures. |
| GET    | `/dashboard/stats`     | Aggregate counts: total, processed, pending, high-priority, department breakdown, priority breakdown. |

All request/response shapes are defined in `backend/schemas.py` and are
browsable interactively at `/docs`.

---

## 5. Database Schema

Table `email_records` (see `database/models.py`):

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `gmail_message_id` | String, unique | Duplicate-processing guard |
| `thread_id` | String | |
| `sender` / `receiver` | String | |
| `subject` / `body` | Text | |
| `has_attachments` | Boolean | |
| `attachment_names` | Text | Comma-separated filenames |
| `received_at` | DateTime | Parsed from the Gmail `Date` header |
| `predicted_category` | String | Raw BERT label (e.g. `billing`) |
| `predicted_department` | String | Human-readable department (e.g. `Finance`) |
| `department_email` | String | Mailbox the email was routed to |
| `confidence` | Float | BERT softmax confidence |
| `sentiment_label` / `sentiment_score` | String / Float | VADER compound score |
| `urgency_level` | String | low / medium / high / critical |
| `priority` | String | low / medium / high (drives dashboard alerts) |
| `routing_status` | String | `pending` → `routed` or `failed` |
| `routed_at` | DateTime | |
| `routing_error` | Text | Populated on forwarding failure, for retry/debugging |
| `processed_at` | DateTime | |
| `processing_time_ms` | Integer | End-to-end classification latency |

---

## 6. Design notes & best practices applied

- **Secrets** live only in `.env` (gitignored); `.env.example` documents
  every variable. Gmail OAuth tokens and client secrets are also gitignored.
- **OAuth**, not password/IMAP credentials, is used for Gmail access.
- **Duplicate-processing guard**: `crud.email_exists()` checks the unique
  `gmail_message_id` before any classification or routing work happens.
- **Error handling / logging**: all backend activity logs to
  `logs/app.log` and stdout; routing failures are stored with their error
  message on the record itself (rather than silently dropped) so they can
  be retried via `POST /route/{id}`.
- **Separation of concerns**: the frontend never touches the database or
  Gmail directly — it only calls the FastAPI REST layer, which is the same
  contract any other client (mobile app, CLI, another service) could use.

## 7. Known limitations / next steps

- The Gmail OAuth flow (`flow.run_local_server`) requires a local browser;
  for a headless/server deployment, swap this for the web-server OAuth
  flow and a proper redirect URI.
- Attachments are currently listed by filename only (`has_attachments`,
  `attachment_names`); downloading/storing the actual attachment bytes is
  not implemented — add this in `gmail_service.py` if needed (Gmail API
  `attachments.get`).
- `forward_email()` sends a new message with the original content quoted
  in the body (a "routed copy") rather than a native Gmail "Forward" —
  this keeps the sending account clear as the sender, which is typically
  required for department inboxes with their own reply threads.
