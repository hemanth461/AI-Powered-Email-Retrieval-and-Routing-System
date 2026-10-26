"""
Enterprise Streamlit Frontend for AI Email Triage & Autonomous Routing System.
Powered by FastAPI, Fine-Tuned BERT, VADER Sentiment, and PostgreSQL.
"""
import os
import sys
import time

# Ensure repository root is in sys.path so backend and database packages can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

raw_backend = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:8000")
BACKEND_URL = raw_backend.replace("localhost", "127.0.0.1")

# ----------------------------------------------------------- Page Config --
st.set_page_config(
    page_title="AutoTriage AI • Intelligent Email Routing",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------- Custom Styling --
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top banner card */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #31104b 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .hero-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(90deg, #ffffff 0%, #c4b5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 15px;
        line-height: 1.5;
        margin-bottom: 14px;
    }

    /* Live pill tags */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
        margin-top: 4px;
    }
    .pill-green {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .pill-blue {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .pill-purple {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }

    /* Modern cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 16px;
        backdrop-filter: blur(10px);
    }
    .glass-card-header {
        font-size: 16px;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Result metric cards */
    .metric-card {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 18px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .metric-value {
        font-size: 22px;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.5px;
    }

    /* Stepper cards */
    .step-box {
        display: flex;
        align-items: center;
        padding: 10px 14px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px dashed rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #cbd5e1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Direct in-process fallback handlers if HTTP endpoint is temporarily unreachable
try:
    from backend.services.classifier_service import classify_email as local_classify_email
except Exception:
    local_classify_email = None

try:
    from database.db import SessionLocal
    from database import crud
except Exception:
    SessionLocal = None
    crud = None

try:
    from backend.services.routing_service import (
        process_unread_emails as local_process_unread,
        simulate_inbound_emails as local_simulate_emails,
        route_all_pending as local_route_all_pending,
    )
except Exception:
    local_process_unread = None
    local_simulate_emails = None
    local_route_all_pending = None

# ------------------------------------------------------------ API Helpers --
def api_get(path, params=None):
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=15.0)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.RequestException as e:
        # Resilient local fallback if backend server is warming up or loopback is unavailable
        if path == "/health":
            if local_classify_email:
                return {"status": "ok", "mode": "in-process"}, None
        elif path == "/dashboard/stats" and crud and SessionLocal:
            try:
                db = SessionLocal()
                stats = crud.get_dashboard_stats(db)
                db.close()
                return stats, None
            except Exception as local_err:
                return None, f"Local stats fallback: {local_err}"
        elif path == "/emails" and crud and SessionLocal:
            try:
                p = params or {}
                db = SessionLocal()
                results, total = crud.list_emails(
                    db,
                    department=p.get("department"),
                    priority=p.get("priority"),
                    routing_status=p.get("routing_status"),
                    search=p.get("search"),
                    limit=int(p.get("limit", 100)),
                    offset=int(p.get("offset", 0)),
                )
                records_dict = [
                    {c.name: getattr(r, c.name) for c in r.__table__.columns}
                    for r in results
                ]
                db.close()
                return {"total": total, "results": records_dict}, None
            except Exception as local_err:
                return None, f"Local email list fallback: {local_err}"

        return None, str(e)


def api_post(path, json=None, params=None):
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=json, params=params, timeout=35.0)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.RequestException as e:
        # Resilient local fallback
        if path == "/classify" and local_classify_email and json:
            try:
                res = local_classify_email(json.get("subject", ""), json.get("body", ""))
                return res, None
            except Exception as local_err:
                return None, f"Local classification error: {local_err}"
        elif path == "/emails/fetch" and local_process_unread and SessionLocal:
            try:
                db = SessionLocal()
                max_r = int((params or {}).get("max_results", 20))
                res = local_process_unread(db, max_results=max_r)
                db.close()
                return res, None
            except Exception as local_err:
                return None, f"Local fetch error: {local_err}"
        elif path == "/emails/simulate" and local_simulate_emails and SessionLocal:
            try:
                db = SessionLocal()
                cnt = int((params or {}).get("count", 5))
                res = local_simulate_emails(db, count=cnt)
                db.close()
                return res, None
            except Exception as local_err:
                return None, f"Local simulation error: {local_err}"
        elif path == "/route/pending/all" and local_route_all_pending and SessionLocal:
            try:
                db = SessionLocal()
                res = local_route_all_pending(db)
                db.close()
                return res, None
            except Exception as local_err:
                return None, f"Local routing error: {local_err}"

        detail = None
        try:
            detail = e.response.json().get("detail")
        except Exception:
            pass
        return None, detail or str(e)


# --------------------------------------------------------------- Sidebar --
with st.sidebar:
    st.markdown("### ⚡ AutoTriage AI")
    st.caption("Autonomous Inbound Email Intelligence")

    health, err = api_get("/health")
    if health and health.get("mode") == "in-process":
        st.markdown(
            '<div class="badge-pill pill-green">🟢 AI Inference Engine Active</div>',
            unsafe_allow_html=True,
        )
    elif health:
        st.markdown(
            '<div class="badge-pill pill-green">🟢 FastAPI Backend Connected</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="badge-pill" style="background:rgba(239,68,68,0.2);color:#f87171;border:1px solid rgba(239,68,68,0.4)">🔴 Backend Unreachable</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🏢 Active Routing Queues")
    departments = [
        ("HR", "hrroutingretrieval@gmail.com", "👥"),
        ("IT", "itroutingretrieval@gmail.com", "💻"),
        ("Finance", "billingroutingretrieval@gmail.com", "💳"),
        ("Sales", "salesroutingretrieval@gmail.com", "📈"),
        ("IT Support", "support@company.com", "🛠️"),
        ("Legal", "legal@company.com", "⚖️"),
        ("Escalations", "escalations@company.com", "🚨"),
    ]
    for name, email, icon in departments:
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 10px; background:rgba(255,255,255,0.02); border-radius:8px; margin-bottom:5px; border:1px solid rgba(255,255,255,0.05);">
                <span style="font-size:13px; font-weight:600;">{icon} {name}</span>
                <span style="font-size:11px; color:#94a3b8; max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{email}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚙️ Architecture Specs")
    st.caption("• **Model:** Fine-Tuned BERT Base (Uncased)\n• **Heuristics:** Hybrid Context Engine\n• **Sentiment:** VADER Lexicon\n• **DB:** PostgreSQL with SQLAlchemy\n• **API:** FastAPI ASGI Server")


# ------------------------------------------------------------- Hero Banner --
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">⚡ Autonomous Email Triage & Routing System</div>
        <div class="hero-subtitle">
            Enterprise-grade email classification engine powered by Fine-Tuned BERT, semantic intent routing, 
            and real-time Gmail dispatch to department mailboxes.
        </div>
        <div>
            <span class="badge-pill pill-green">✓ Neural Classifier Active</span>
            <span class="badge-pill pill-blue">✓ Gmail API OAuth 2.0</span>
            <span class="badge-pill pill-purple">✓ PostgreSQL Audit Ledger</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["⚡ Live AI Playground", "📥 Gmail Automation", "📊 Executive Analytics", "🔍 Audit Ledger & History"]
)

# --------------------------------------------- Tab 1: Live AI Playground --
with tab1:
    col_left, col_right = st.columns([1.1, 0.9], gap="large")

    if "preset_version" not in st.session_state:
        st.session_state.preset_version = 0
    if "subj_input" not in st.session_state:
        st.session_state.subj_input = "Taking tomorrow off for family emergency"
    if "body_input" not in st.session_state:
        st.session_state.body_input = (
            "Hi, I won't be able to log in tomorrow as I need to travel back to my hometown for an urgent "
            "family medical matter. I will be on casual time off and back on Monday."
        )

    def load_preset(s, b):
        st.session_state.subj_input = s
        st.session_state.body_input = b
        st.session_state.preset_version += 1

    with col_left:
        st.markdown("#### 📝 Classify Inbound Message")
        st.caption("Test classification accuracy using your own message or click a pre-filled sample:")

        # Quick preset buttons
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            if st.button("👥 HR Leave", use_container_width=True):
                load_preset(
                    "Taking tomorrow off for family emergency",
                    "Hi, I won't be able to log in tomorrow as I need to travel back to my hometown for an urgent family medical matter. I will be on casual time off and back on Monday.",
                )
                st.rerun()
        with p2:
            if st.button("💻 IT Hardware", use_container_width=True):
                load_preset(
                    "Workstation screen turned blue and crashed",
                    "When I booted my workstation laptop today it showed a blue screen error and shut down. Can someone inspect the machine or arrange a hardware replacement?",
                )
                st.rerun()
        with p3:
            if st.button("📈 Sales Quote", use_container_width=True):
                load_preset(
                    "Looking to evaluate the platform for 50 users",
                    "Hello, our organization is expanding rapidly. What are the annual subscription costs for 50 seats, and could we schedule a walkthrough demo this Thursday?",
                )
                st.rerun()
        with p4:
            if st.button("💳 Billing / Refund", use_container_width=True):
                load_preset(
                    "Extra 200 dollars debited from my Mastercard",
                    "Hi, my bank statement shows two identical deductions of $199 on September 12. Could you please reverse the second transaction and send an updated receipt?",
                )
                st.rerun()

        subject = st.text_input(
            "Email Subject:",
            value=st.session_state.subj_input,
            key=f"subj_widget_{st.session_state.preset_version}",
            placeholder="e.g. Request for software license upgrade",
        )
        body = st.text_area(
            "Email Body:",
            value=st.session_state.body_input,
            key=f"body_widget_{st.session_state.preset_version}",
            height=180,
            placeholder="Paste email body or draft message...",
        )

        classify_clicked = st.button("🚀 Analyze & Predict Route", type="primary", use_container_width=True)

    with col_right:
        st.markdown("#### 🎯 Classification Breakdown")
        if classify_clicked:
            clean_subj = (subject or "").strip()
            clean_body = (body or "").strip()
            if clean_subj or clean_body:
                with st.spinner("Running neural inference & sentiment engine..."):
                    result, err = api_post("/classify", json={"subject": clean_subj, "body": clean_body})

                if err:
                    st.error(f"❌ Classification error: {err}")
                else:
                    cat = result["category"].upper()
                    dept = result["department_name"]
                    target_email = result["department_email"]
                    conf = result["confidence"] * 100
                    prio = result["priority"].upper()
                    sent = result["sentiment_label"].upper()

                    # Color map for priority
                    prio_colors = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}
                    prio_color = prio_colors.get(prio, "#3b82f6")

                    st.markdown(
                        f"""
                        <div class="glass-card" style="border-left: 5px solid {prio_color};">
                            <div style="font-size:13px; text-transform:uppercase; color:#94a3b8; font-weight:700;">Predicted Routing Destination</div>
                            <div style="font-size:24px; font-weight:800; color:#f8fafc; margin-top:2px;">{dept} Department</div>
                            <div style="font-size:13px; color:#c4b5fd; margin-bottom:12px;">📬 Forwarding to: <b>{target_email}</b></div>
                            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                                <span class="badge-pill pill-blue">Confidence: {conf:.1f}%</span>
                                <span class="badge-pill" style="background:{prio_color}22; color:{prio_color}; border:1px solid {prio_color}66;">Priority: {prio}</span>
                                <span class="badge-pill pill-purple">Sentiment: {sent}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Category probability bar chart
                    st.markdown("##### Model Probability Distribution")
                    prob_data = [
                        {"Category": c.replace("_", " ").title(), "Probability": round(p * 100, 1)}
                        for c, p in sorted(result["category_probs"].items(), key=lambda x: x[1], reverse=True)[:5]
                    ]
                    df_prob = pd.DataFrame(prob_data)
                    fig = px.bar(
                        df_prob,
                        x="Probability",
                        y="Category",
                        orientation="h",
                        color="Probability",
                        color_continuous_scale="Purples",
                        text="Probability",
                    )
                    fig.update_layout(
                        height=220,
                        margin=dict(l=0, r=20, t=10, b=10),
                        xaxis_title="Confidence (%)",
                        yaxis_title="",
                        showlegend=False,
                        coloraxis_showscale=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#94a3b8"),
                    )
                    fig.update_traces(texttemplate="%{text}%", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)

                    if result.get("urgency_keywords"):
                        st.caption(f"🚨 **Detected Urgency Triggers:** {', '.join(result['urgency_keywords'])}")
            else:
                st.warning("⚠️ Please provide a subject or body to analyze.")
        else:
            st.info("👈 Enter an email on the left or select a sample preset to see real-time classification.")


# ------------------------------------------- Tab 2: Gmail Automation --
with tab2:
    st.markdown("#### 📥 Gmail Inbox Monitor & Auto-Dispatcher")
    st.caption("Continuously monitors your configured inbox via Gmail API OAuth2, strips HTML, runs inference, and automatically forwards emails to target department queues.")

    c1, c2 = st.columns([1, 1.2], gap="large")

    with c1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="glass-card-header">⚙️ Inbound Execution Controls</div>', unsafe_allow_html=True)
        max_fetch = st.slider("Maximum unread emails to inspect per run:", 1, 50, 15)
        st.caption("Fetches messages matching `labelIds: ['UNREAD', 'INBOX']` via Gmail API v1.")
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            fetch_now = st.button("⚡ Live Gmail Sync", type="primary", use_container_width=True)
        with btn_col2:
            simulate_now = st.button("🧪 Simulate 5 Inbound Emails", use_container_width=True)

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        route_pending_now = st.button("🚀 Dispatch All Pending Emails to Mailboxes", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="glass-card-header">🔄 Pipeline Execution Sequence</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="step-box"><span>1️⃣</span> <span style="margin-left:8px;"><b>Inbound Ingestion:</b> Poll live Gmail batch or ingest synthetic sample</span></div>
            <div class="step-box"><span>2️⃣</span> <span style="margin-left:8px;"><b>Sanitization:</b> Strip HTML tags, inline styles, and unescape entities</span></div>
            <div class="step-box"><span>3️⃣</span> <span style="margin-left:8px;"><b>Neural Classification:</b> Contextual categorization & domain verification</span></div>
            <div class="step-box"><span>4️⃣</span> <span style="margin-left:8px;"><b>Sentiment & Urgency:</b> Score urgency triggers and assign ticket priority</span></div>
            <div class="step-box"><span>5️⃣</span> <span style="margin-left:8px;"><b>Ledger & Routing:</b> Persist to PostgreSQL and forward to department queue</span></div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if fetch_now or simulate_now:
        endpoint = "/emails/fetch" if fetch_now else "/emails/simulate"
        params = {"max_results": max_fetch} if fetch_now else {"count": 5}
        with st.spinner("Processing inbound batch through classification & routing pipeline..."):
            res, err = api_post(endpoint, params=params)

        if err:
            st.error(f"❌ Inbound pipeline error: {err}")
            if "credentials" in err.lower() or "oauth" in err.lower():
                with st.expander("🔑 How to link your real Gmail account to Render (2 Minutes)"):
                    st.markdown(
                        """
                        Your live Gmail OAuth tokens are kept secure on your local computer (`credentials/` folder) 
                        and are git-ignored for safety. To enable live Gmail fetching in Render:
                        
                        1. Go to your **[Render Dashboard](https://dashboard.render.com)**.
                        2. Click **AI-Powered-Email-Retrieval-and-Routing-System** > **Environment**.
                        3. Scroll down to **Secret Files** and click **Add Secret File**.
                        4. Add your two credential files:
                           * **File 1:** `credentials/gmail_credentials.json`
                           * **File 2:** `credentials/gmail_token.json`
                        5. Click **Save Changes** — Render will automatically restart and connect to your inbox!
                        
                        💡 *In the meantime, click **'🧪 Simulate 5 Inbound Emails'** above to test the live pipeline, database storage, and dashboard analytics!*
                        """
                    )
        else:
            mode_text = "Live Gmail Inbound" if fetch_now else "Simulated Inbound Batch"
            st.success(f"✅ {mode_text} successfully triaged and recorded into PostgreSQL!")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#60a5fa">{res["fetched"]}</div><div class="metric-label">Fetched</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#a855f7">{res["new"]}</div><div class="metric-label">New Processed</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#94a3b8">{res["duplicates"]}</div><div class="metric-label">Duplicates Skipped</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10b981">{res["routed"]}</div><div class="metric-label">Auto-Routed</div></div>', unsafe_allow_html=True)
            with m5:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#ef4444">{res["failed"]}</div><div class="metric-label">Failures</div></div>', unsafe_allow_html=True)

    if route_pending_now:
        with st.spinner("Dispatching unrouted emails to department mailboxes..."):
            p_res, p_err = api_post("/route/pending/all")
        if p_err:
            st.error(f"❌ Dispatch failed: {p_err}")
        else:
            tot = p_res.get("total", 0)
            routed = p_res.get("routed", 0)
            failed = p_res.get("failed", 0)
            if tot == 0:
                st.info("ℹ️ All records in the database have already been successfully routed.")
            elif failed > 0:
                st.warning(f"⚠️ Routed {routed} of {tot} pending emails. {failed} encountered an error.")
            else:
                st.success(f"🎉 Successfully routed and forwarded {routed} pending emails to target department queues!")
            time.sleep(1)
            st.rerun()


# ----------------------------------------- Tab 3: Executive Analytics --
with tab3:
    st.markdown("#### 📊 Triage Performance & Department Metrics")

    stats, err = api_get("/dashboard/stats")
    if err:
        st.error(f"❌ Dashboard analytics unavailable: {err}")
    else:
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#c084fc">{stats["total_emails"]}</div><div class="metric-label">Total Volume</div></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10b981">{stats["processed_emails"]}</div><div class="metric-label">Processed</div></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#f59e0b">{stats["pending_emails"]}</div><div class="metric-label">Pending Review</div></div>', unsafe_allow_html=True)
        with k4:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#ef4444">{stats["high_priority_emails"]}</div><div class="metric-label">High Priority</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ch1, ch2 = st.columns(2, gap="large")

        with ch1:
            st.markdown("##### 🏢 Inbound Volume by Department")
            if stats.get("department_counts"):
                dept_df = pd.DataFrame(list(stats["department_counts"].items()), columns=["Department", "Count"])
                fig_dept = px.bar(
                    dept_df,
                    x="Department",
                    y="Count",
                    color="Count",
                    color_continuous_scale="Purples",
                    text="Count",
                )
                fig_dept.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_dept, use_container_width=True)
            else:
                st.info("No department stats collected yet.")

        with ch2:
            st.markdown("##### 🚨 Priority Tier Breakdown")
            if stats.get("priority_counts"):
                p_counts = stats["priority_counts"]
                fig_pie = go.Figure(
                    data=[
                        go.Pie(
                            labels=list(p_counts.keys()),
                            values=list(p_counts.values()),
                            hole=0.55,
                            marker_colors=["#ef4444", "#f59e0b", "#10b981"],
                        )
                    ]
                )
                fig_pie.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8"),
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No priority metrics logged yet.")

    if st.button("🔄 Refresh Analytics", use_container_width=False):
        st.rerun()


# ----------------------------------- Tab 4: Audit Ledger & History --
with tab4:
    st.markdown("#### 🔍 Historical Email Audit Ledger")
    st.caption("Search, filter, and inspect persisted email triage records and routing execution results.")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        f_dept = st.text_input("Filter Department:", placeholder="e.g. HR, Sales, IT")
    with f2:
        f_prio = st.selectbox("Priority:", ["Any", "high", "medium", "low"])
    with f3:
        f_status = st.selectbox("Routing Status:", ["Any", "routed", "pending", "failed"])
    with f4:
        f_search = st.text_input("Keyword Search:", placeholder="Subject, sender, or body...")

    filter_params = {"limit": 200}
    if f_dept:
        filter_params["department"] = f_dept
    if f_prio != "Any":
        filter_params["priority"] = f_prio
    if f_status != "Any":
        filter_params["routing_status"] = f_status
    if f_search:
        filter_params["search"] = f_search

    records, err = api_get("/emails", params=filter_params)
    if err:
        st.error(f"❌ Failed to load ledger: {err}")
    elif records:
        total_found = records.get("total", 0)
        results = records.get("results", [])

        st.markdown(f"**Found {total_found} historical records**")
        if results:
            df = pd.DataFrame(results)

            pending_items = [r for r in results if r.get("routing_status") == "pending"]
            if pending_items:
                b1, b2 = st.columns([3, 1])
                with b1:
                    st.warning(f"⚠️ **{len(pending_items)} email(s) are pending department dispatch.**")
                with b2:
                    if st.button("🚀 Route Pending Now", type="primary", use_container_width=True, key="tab4_route_btn"):
                        with st.spinner("Dispatching to mailboxes..."):
                            d_res, d_err = api_post("/route/pending/all")
                        if d_err:
                            st.error(f"Routing failed: {d_err}")
                        else:
                            st.success(f"Dispatched {d_res.get('routed', 0)} email(s)!")
                            time.sleep(1)
                            st.rerun()

            # Style display dataframe
            cols = [
                "id",
                "sender",
                "subject",
                "predicted_department",
                "priority",
                "sentiment_label",
                "routing_status",
                "routing_error",
                "processed_at",
            ]
            cols = [c for c in cols if c in df.columns]

            st.dataframe(
                df[cols],
                use_container_width=True,
                height=380,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "sender": st.column_config.TextColumn("Sender", width="medium"),
                    "subject": st.column_config.TextColumn("Subject", width="large"),
                    "predicted_department": st.column_config.TextColumn("Department", width="small"),
                    "priority": st.column_config.TextColumn("Priority", width="small"),
                    "sentiment_label": st.column_config.TextColumn("Sentiment", width="small"),
                    "routing_status": st.column_config.TextColumn("Status", width="small"),
                    "routing_error": st.column_config.TextColumn("Routing Notes", width="medium"),
                    "processed_at": st.column_config.DatetimeColumn("Processed At", format="YYYY-MM-DD HH:mm"),
                },
            )

            c_down, _ = st.columns([1, 3])
            with c_down:
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Export Audit Ledger as CSV",
                    data=csv_data,
                    file_name="email_triage_audit.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.info("No records matched the selected query filters.")

# --------------------------------------------------------------- Footer --
st.markdown("<br><hr style='border-color:rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; color:#64748b; font-size:12px;">
        <span>⚡ AutoTriage AI • Enterprise Mailbox Routing Engine</span>
        <span>FastAPI • Fine-Tuned BERT • VADER • PostgreSQL • Streamlit</span>
    </div>
    """,
    unsafe_allow_html=True,
)
