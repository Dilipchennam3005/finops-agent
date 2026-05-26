"""
FinOps Agent — Streamlit Frontend (v0.5)
Run: streamlit run streamlit_app/app.py
"""
import importlib.util
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

st.set_page_config(
    page_title="FinOps Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp, [data-testid="stApp"] {
    background-color: #0A0A0A !important;
    font-family: Inter, system-ui, -apple-system, sans-serif !important;
    color: #ECECEC !important;
}
#MainMenu, footer { visibility: hidden !important; }
header[data-testid="stHeader"] { display: none !important; }

.block-container {
    padding: 2rem 2.5rem 4rem 2.5rem !important;
    max-width: 100% !important;
}

p, span, li, td, th, div, label {
    font-family: Inter, system-ui, sans-serif !important;
}
h1, h2, h3, h4 {
    font-family: Inter, system-ui, sans-serif !important;
    color: #ECECEC !important;
}

/* ── Sidebar ───────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #0A0A0A !important;
    border-right: 1px solid #2E2E2E !important;
}
section[data-testid="stSidebar"] > div:first-child {
    background-color: #0A0A0A !important;
    padding-top: 1.25rem !important;
}
section[data-testid="stSidebar"] * { color: #ECECEC !important; }
section[data-testid="stSidebar"] hr { border-color: #2E2E2E !important; }

/* ── Buttons ──────────────────────────────── */
.stButton > button {
    background-color: #D97757 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    transition: background-color 0.15s !important;
}
.stButton > button:hover  { background-color: #C06444 !important; }
.stButton > button:disabled {
    background-color: #1A1A1A !important;
    color: #555 !important;
    border: 1px solid #2E2E2E !important;
}

/* ── Number input ─────────────────────────── */
.stNumberInput input {
    background-color: #1A1A1A !important;
    border: 1px solid #2E2E2E !important;
    color: #ECECEC !important;
    border-radius: 6px !important;
}
.stNumberInput input:focus {
    border-color: #D97757 !important;
    box-shadow: 0 0 0 1px rgba(217,119,87,0.4) !important;
}
.stNumberInput label {
    color: #8A8A8A !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── File uploader ────────────────────────── */
[data-testid="stFileUploader"] {
    background-color: #1A1A1A !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"] label {
    color: #8A8A8A !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
[data-testid="stFileUploaderDropzone"] {
    background-color: #111 !important;
    border: 1px dashed #2E2E2E !important;
    border-radius: 6px !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #D97757 !important;
    background-color: rgba(217,119,87,0.03) !important;
}
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span { color: #555 !important; }

/* ── Alerts ───────────────────────────────── */
[data-testid="stAlert"] {
    background-color: #1A1A1A !important;
    border: 1px solid #2E2E2E !important;
    border-radius: 8px !important;
}

/* ── Expander ─────────────────────────────── */
[data-testid="stExpander"] {
    background-color: #1A1A1A !important;
    border: 1px solid #2E2E2E !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary { color: #ECECEC !important; }
details > summary { color: #ECECEC !important; }

/* ── Dividers ─────────────────────────────── */
hr { border-color: #2E2E2E !important; margin: 1.25rem 0 !important; }

/* ── Download button ──────────────────────── */
[data-testid="stDownloadButton"] > button {
    background-color: #D97757 !important;
    color: white !important;
}

/* ── Plotly chart card ────────────────────── */
[data-testid="stPlotlyChart"] {
    background-color: #1A1A1A !important;
    border: 1px solid #2E2E2E !important;
    border-radius: 10px !important;
    padding: 0.25rem !important;
}

/* ── Status widget ────────────────────────── */
[data-testid="stStatusWidget"] { background-color: #1A1A1A !important; border: 1px solid #2E2E2E !important; border-radius: 8px !important; }
.stStatus { background-color: #1A1A1A !important; }

/* ══ Component styles ══════════════════════════════════════════════════════ */

.fo-header {
    display: flex; align-items: center; gap: 16px;
    padding: 0 0 2rem 0; border-bottom: 1px solid #2E2E2E; margin-bottom: 2.5rem;
}
.fo-app-name  { font-size: 28px; font-weight: 700; color: #ECECEC; letter-spacing: -0.02em; margin: 0; line-height: 1.1; }
.fo-subtitle  { font-size: 13px; color: #8A8A8A; margin: 4px 0 0 0; }
.fo-vbadge    {
    background: rgba(217,119,87,0.12); color: #D97757;
    border: 1px solid rgba(217,119,87,0.28); border-radius: 20px;
    padding: 2px 10px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
    display: inline-block; margin-left: 6px; vertical-align: middle;
}

.fo-section   {
    font-size: 10px; font-weight: 700; color: #D97757;
    text-transform: uppercase; letter-spacing: 0.1em;
    padding-bottom: 0.6rem; border-bottom: 1px solid #2E2E2E;
    margin: 2rem 0 1.25rem 0;
}

/* Metric grid */
.fo-metrics { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 2.5rem; }
.fo-card {
    background: #1A1A1A; border: 1px solid #2E2E2E; border-radius: 10px;
    padding: 1.25rem 1.5rem; position: relative; overflow: hidden;
}
.fo-card::before { content:''; position:absolute; inset:0 auto 0 0; width:3px; border-radius:10px 0 0 10px; }
.fo-card.orange::before { background:#D97757; }
.fo-card.green::before  { background:#2ECC71; }
.fo-card.yellow::before { background:#F39C12; }
.fo-card.red::before    { background:#E74C3C; }
.fo-val   { font-size: 36px; font-weight: 700; color: #ECECEC; letter-spacing: -0.03em; line-height: 1; margin-bottom: 6px; }
.fo-lbl   { font-size: 11px; color: #8A8A8A; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.fo-sub   { font-size: 11px; color: #555; margin-top: 5px; }

/* Exception table */
.fo-tbl-wrap { background:#1A1A1A; border:1px solid #2E2E2E; border-radius:10px; overflow:auto; margin-bottom:2rem; }
.fo-tbl { width:100%; border-collapse:collapse; font-size:13px; }
.fo-tbl thead tr { background:#111; border-bottom:1px solid #2E2E2E; }
.fo-tbl thead th {
    padding:11px 14px; text-align:left;
    font-size:10px; font-weight:700; color:#D97757;
    text-transform:uppercase; letter-spacing:0.07em; white-space:nowrap;
}
.fo-tbl tbody tr { border-bottom:1px solid rgba(255,255,255,0.04); }
.fo-tbl tbody tr:nth-child(even) { background:rgba(255,255,255,0.018); }
.fo-tbl tbody tr:hover { background:rgba(217,119,87,0.045); }
.fo-tbl tbody tr:last-child { border-bottom:none; }
.fo-tbl td { padding:12px 14px; color:#ECECEC; vertical-align:top; }
.fo-tbl td.dim  { color:#8A8A8A; font-size:12px; }
.fo-tbl td.mono { font-family:'Fira Code','Courier New',monospace; font-size:12px; }
.fo-tbl td.wrap { white-space:normal; min-width:200px; max-width:340px; line-height:1.55; font-size:12px; }
.fo-tbl td.num  { font-family:'Fira Code','Courier New',monospace; white-space:nowrap; }

/* Badges */
.badge { display:inline-block; padding:3px 9px; border-radius:20px; font-size:11px; font-weight:600; letter-spacing:0.03em; white-space:nowrap; }
.b-green  { background:rgba(46,204,113,0.12);  color:#2ECC71; border:1px solid rgba(46,204,113,0.25); }
.b-yellow { background:rgba(243,156,18,0.12);  color:#F39C12; border:1px solid rgba(243,156,18,0.25); }
.b-red    { background:rgba(231,76,60,0.12);   color:#E74C3C; border:1px solid rgba(231,76,60,0.25); }
.b-orange { background:rgba(217,119,87,0.12);  color:#D97757; border:1px solid rgba(217,119,87,0.25); }
.b-gray   { background:rgba(138,138,138,0.08); color:#8A8A8A; border:1px solid rgba(138,138,138,0.18); }
.b-blue   { background:rgba(52,152,219,0.12);  color:#3498DB; border:1px solid rgba(52,152,219,0.25); }

/* Review cards */
.rv-card {
    background:#1A1A1A; border:1px solid #2E2E2E; border-left:3px solid #D97757;
    border-radius:10px; padding:1.25rem 1.5rem; margin-bottom:1rem;
}
.rv-hdr  { display:flex; align-items:center; gap:10px; margin-bottom:0.85rem; flex-wrap:wrap; }
.rv-acct { font-size:15px; font-weight:600; color:#ECECEC; font-family:'Fira Code','Courier New',monospace; }
.rv-meta { font-size:12px; color:#8A8A8A; }
.rv-grid { display:grid; grid-template-columns:1fr 1fr; gap:1.25rem; }
.rv-lbl  { font-size:10px; font-weight:700; color:#8A8A8A; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:5px; }
.rv-val  { font-size:13px; color:#ECECEC; line-height:1.55; }
.rv-cases { margin-top:0.85rem; font-size:12px; color:#8A8A8A; }
.rv-cases .ct { color:#D97757; font-family:monospace; font-size:11px; background:rgba(217,119,87,0.08); padding:1px 6px; border-radius:3px; margin-right:4px; }

/* Sidebar logo */
.sb-logo { display:flex; align-items:center; gap:10px; padding:0 0 1.5rem 0; border-bottom:1px solid #2E2E2E; margin-bottom:0.25rem; }
.sb-name { font-size:15px; font-weight:700; color:#ECECEC; }
.sb-ver  { font-size:10px; color:#8A8A8A; }
.sb-sec  { font-size:10px; font-weight:700; color:#D97757; text-transform:uppercase; letter-spacing:0.1em; margin:1.5rem 0 0.75rem 0; }

/* Empty state */
.empty { text-align:center; padding:5rem 2rem; }
.empty-title { font-size:18px; font-weight:600; color:#ECECEC; margin-bottom:0.5rem; }
.empty-sub   { font-size:14px; color:#8A8A8A; line-height:1.6; }

/* Success bar */
.success-bar {
    background:rgba(46,204,113,0.08); border:1px solid rgba(46,204,113,0.2);
    border-left:3px solid #2ECC71; border-radius:8px; padding:0.85rem 1.25rem;
    color:#2ECC71; font-size:13px; font-weight:500;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
VECTOR_STORE_PATH = str(ROOT / "data" / "vector_store")
KB_COLLECTION     = "finops_exceptions"


def _kb_count() -> int:
    try:
        import chromadb
        return chromadb.PersistentClient(path=VECTOR_STORE_PATH).get_collection(KB_COLLECTION).count()
    except Exception:
        return 0


def _build_kb() -> None:
    spec = importlib.util.spec_from_file_location(
        "build_knowledge_base", ROOT / "data" / "build_knowledge_base.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.build(VECTOR_STORE_PATH)


def _reset_run():
    st.session_state.run_complete = False
    st.session_state.run_error    = None
    st.session_state.results      = None


def _conf_badge(c: float) -> str:
    if c >= 0.8:  return f'<span class="badge b-green">{c:.0%}</span>'
    if c >= 0.65: return f'<span class="badge b-yellow">{c:.0%}</span>'
    return            f'<span class="badge b-red">{c:.0%}</span>'


def _type_badge(t: str) -> str:
    cls = {"FX_DISCREPANCY": "b-yellow", "GL_MISMATCH": "b-red",
           "GL_ONLY": "b-orange", "SUBLEDGER_ONLY": "b-blue"}.get(t, "b-gray")
    return f'<span class="badge {cls}">{escape(t)}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in {"gl_path": None, "sl_path": None, "using_sample": False,
              "run_complete": False, "run_error": None, "results": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
_LOGO_SVG = """
<svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
  <polygon points="18,2 33,10 33,26 18,34 3,26 3,10" fill="#D97757"/>
  <text x="18" y="22" font-family="Inter,system-ui,sans-serif" font-size="11"
        font-weight="700" fill="white" text-anchor="middle" dominant-baseline="middle">FO</text>
</svg>"""

with st.sidebar:
    st.markdown(f"""
    <div class="sb-logo">
      {_LOGO_SVG}
      <div>
        <div class="sb-name">FinOps Agent</div>
        <div class="sb-ver">v0.5 · AI reconciliation</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Data source ──────────────────────────────────────────────────────────
    st.markdown('<div class="sb-sec">Data Source</div>', unsafe_allow_html=True)

    gl_file = st.file_uploader("GL Balances CSV",  type="csv", key="gl_upload", on_change=_reset_run)
    sl_file = st.file_uploader("Subledger CSV",    type="csv", key="sl_upload", on_change=_reset_run)

    st.markdown("<div style='text-align:center;color:#555;font-size:11px;margin:0.5rem 0'>— or —</div>",
                unsafe_allow_html=True)

    if st.button("Use Sample Data", use_container_width=True):
        st.session_state.gl_path = str(ROOT / "data" / "raw" / "gl_balances.csv")
        st.session_state.sl_path = str(ROOT / "data" / "raw" / "subledger.csv")
        st.session_state.using_sample = True
        _reset_run()
        st.rerun()

    # Handle file saves
    raw_dir = ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    if gl_file is not None:
        p = raw_dir / "uploaded_gl.csv"; p.write_bytes(gl_file.getvalue())
        st.session_state.gl_path = str(p); st.session_state.using_sample = False; _reset_run()
    if sl_file is not None:
        p = raw_dir / "uploaded_sl.csv"; p.write_bytes(sl_file.getvalue())
        st.session_state.sl_path = str(p); st.session_state.using_sample = False; _reset_run()

    # Data status
    if st.session_state.gl_path and st.session_state.sl_path:
        src = "Sample data" if st.session_state.using_sample else "Uploaded files"
        st.markdown(f"""
        <div style="background:rgba(46,204,113,0.08);border:1px solid rgba(46,204,113,0.2);
                    border-radius:6px;padding:0.6rem 0.85rem;margin-top:0.5rem;">
          <span style="color:#2ECC71;font-size:12px;font-weight:500;">&#10003; {escape(src)} loaded</span>
        </div>""", unsafe_allow_html=True)
    else:
        missing = " + ".join(n for n, p in [("GL", st.session_state.gl_path),
                                              ("Subledger", st.session_state.sl_path)] if not p)
        st.markdown(f"""
        <div style="background:rgba(138,138,138,0.06);border:1px solid #2E2E2E;
                    border-radius:6px;padding:0.6rem 0.85rem;margin-top:0.5rem;">
          <span style="color:#8A8A8A;font-size:12px;">Missing: {escape(missing)}</span>
        </div>""", unsafe_allow_html=True)

    # ── Settings ─────────────────────────────────────────────────────────────
    st.markdown('<div class="sb-sec">Settings</div>', unsafe_allow_html=True)
    threshold = st.number_input(
        "Variance Threshold (USD)",
        min_value=1_000, max_value=500_000, value=10_000, step=1_000,
        help="Flag exceptions above this USD amount",
    )

    # ── Run ──────────────────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
    data_ready = bool(st.session_state.gl_path and st.session_state.sl_path)
    run_clicked = st.button(
        "Run Reconciliation",
        type="primary",
        disabled=not data_ready,
        use_container_width=True,
    )

    st.divider()
    st.markdown("""
    <div style="font-size:10px;color:#555;line-height:1.8;">
      LangGraph · ChromaDB · Claude API<br>
      <a href="https://github.com/Dilipchennam3005/finops-agent"
         style="color:#D97757;text-decoration:none;">github.com / finops-agent</a>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA — Header
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="fo-header">
  {_LOGO_SVG.replace('width="36" height="36"', 'width="44" height="44"')}
  <div>
    <div style="display:flex;align-items:center;gap:10px;">
      <span class="fo-app-name">FinOps Agent</span>
      <span class="fo-vbadge">v0.5</span>
    </div>
    <p class="fo-subtitle">Financial Reconciliation Intelligence</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE EXECUTION
# ══════════════════════════════════════════════════════════════════════════════
if run_clicked and data_ready:
    _reset_run()

    from agents.reconciliation_agent import run_matching_engine
    from agents.investigation_agent  import investigation_agent
    from agents.orchestrator import FinOpsState, reporting_agent, human_review_node

    state: FinOpsState = {
        "raw_data": {}, "exceptions": [], "investigations": [],
        "report": "", "confidence": 0.0, "human_review": False,
    }
    pipeline_ok = True

    with st.status("Running pipeline...", expanded=True) as status:

        # KB check
        if _kb_count() == 0:
            status.write("**Building knowledge base** — first-run setup (32 historical records)...")
            try:
                _build_kb()
                status.write(f"  Knowledge base ready — {_kb_count()} records")
            except Exception as exc:
                status.write(f"  KB build failed: {type(exc).__name__}: {exc}")

        # Agent 1
        status.write("**Agent 1 · Reconciliation** — matching GL vs Subledger...")
        try:
            recon = run_matching_engine(
                gl_path=st.session_state.gl_path,
                subledger_path=st.session_state.sl_path,
                output_dir=str(ROOT / "data" / "processed"),
                threshold=float(threshold),
            )
            state["exceptions"] = recon["exceptions"]
            state["raw_data"]   = {
                "total_accounts" : recon["total_accounts"],
                "matched_count"  : recon["matched_count"],
                "exception_count": recon["exception_count"],
                "threshold_usd"  : recon["threshold_usd"],
            }
            status.write(
                f"  Matched **{recon['matched_count']}/{recon['total_accounts']}** accounts — "
                f"**{recon['exception_count']}** exceptions above ${recon['threshold_usd']:,.0f}"
            )
        except Exception as exc:
            st.session_state.run_error = f"{type(exc).__name__}: {exc}"
            status.update(label="Reconciliation failed", state="error")
            pipeline_ok = False

        # Agent 2
        if pipeline_ok:
            status.write(
                f"**Agent 2 · Investigation** — analysing {len(state['exceptions'])} "
                "exceptions with RAG + Claude..."
            )
            try:
                state = investigation_agent(state)
                status.write(
                    f"  Investigated **{len(state['investigations'])}** exceptions — "
                    f"avg confidence **{state['confidence']:.0%}**"
                )
            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}"
                status.write(f"  Investigation unavailable — {err}")
                state["investigations"] = [
                    {"account": ex["account"], "exception_type": ex["type"],
                     "variance": ex["variance"], "currency": ex["currency"],
                     "root_cause": f"Investigation unavailable: {err}",
                     "recommended_action": "Manual review required",
                     "confidence": 0.5, "exception_category": "OTHER", "similar_cases": []}
                    for ex in state["exceptions"]
                ]
                state["confidence"] = 0.5

        # Agent 3
        if pipeline_ok:
            status.write("**Agent 3 · Reporting** — generating report...")
            state = human_review_node(state) if state["confidence"] < 0.8 else reporting_agent(state)
            status.write("  Report generated")
            status.update(label="Pipeline complete", state="complete")

    if pipeline_ok:
        st.session_state.results      = state
        st.session_state.run_complete = True
        st.rerun()

if st.session_state.run_error:
    st.error(f"Pipeline error: {st.session_state.run_error}")

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.run_complete and st.session_state.results:
    state = st.session_state.results
    raw   = state["raw_data"]
    invs  = state["investigations"]
    excs  = state["exceptions"]
    conf  = state["confidence"]

    # ── Metric cards ──────────────────────────────────────────────────────────
    total = raw.get("total_accounts", 0)
    clean = raw.get("matched_count", 0)
    exc_n = raw.get("exception_count", 0)
    thr   = raw.get("threshold_usd", 0)
    pct   = f"{clean/total*100:.0f}% of total" if total else ""
    conf_card_cls = "green" if conf >= 0.8 else "red"
    conf_delta    = "auto-approved" if conf >= 0.8 else "needs review"
    conf_delta_col= "#2ECC71" if conf >= 0.8 else "#E74C3C"

    st.markdown(f"""
    <div class="fo-metrics">
      <div class="fo-card orange">
        <div class="fo-val">{total}</div>
        <div class="fo-lbl">Total Accounts</div>
      </div>
      <div class="fo-card green">
        <div class="fo-val">{clean}</div>
        <div class="fo-lbl">Clean Reconciliations</div>
        <div class="fo-sub">{pct}</div>
      </div>
      <div class="fo-card yellow">
        <div class="fo-val">{exc_n}</div>
        <div class="fo-lbl">Exceptions Found</div>
        <div class="fo-sub">&gt;${thr:,.0f} USD threshold</div>
      </div>
      <div class="fo-card {conf_card_cls}">
        <div class="fo-val">{conf:.0%}</div>
        <div class="fo-lbl">Avg Confidence</div>
        <div class="fo-sub" style="color:{conf_delta_col};">{conf_delta}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Exceptions table ──────────────────────────────────────────────────────
    st.markdown('<div class="fo-section">Exception Details</div>', unsafe_allow_html=True)

    if invs:
        has_similar = any(
            isinstance(inv.get("similar_cases"), list) and inv["similar_cases"] for inv in invs
        )
        sim_th = "<th>Similar Cases</th>" if has_similar else ""

        rows = ""
        for inv in invs:
            sim_td = ""
            if has_similar:
                cases = inv.get("similar_cases") or []
                sim_td = f'<td class="dim mono">{escape(", ".join(cases))}</td>'

            rows += f"""
            <tr>
              <td class="mono">{escape(str(inv["account"]))}</td>
              <td>{_type_badge(inv["exception_type"])}</td>
              <td class="dim">{escape(str(inv["currency"]))}</td>
              <td class="num">${float(inv["variance"]):,.0f}</td>
              <td>{escape(str(inv.get("exception_category","—")))}</td>
              <td class="wrap">{escape(str(inv["root_cause"]))}</td>
              <td class="wrap">{escape(str(inv["recommended_action"]))}</td>
              <td>{_conf_badge(float(inv["confidence"]))}</td>
              {sim_td}
            </tr>"""

        st.markdown(f"""
        <div class="fo-tbl-wrap">
          <table class="fo-tbl">
            <thead><tr>
              <th>Account</th><th>Exception Type</th><th>Currency</th>
              <th>Variance (USD)</th><th>AI Category</th>
              <th>Root Cause</th><th>Recommended Action</th>
              <th>Confidence</th>{sim_th}
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown('<div class="fo-section">Exception Analytics</div>', unsafe_allow_html=True)

    if excs:
        type_df = (
            pd.DataFrame(excs).groupby("type").size()
            .reset_index(name="Count").rename(columns={"type": "Exception Type"})
        )

        # Bar chart — dark theme, orange bars
        fig_bar = px.bar(
            type_df, x="Exception Type", y="Count", text="Count",
            color_discrete_sequence=["#D97757"],
            title="Exceptions by Type",
        )
        fig_bar.update_layout(
            paper_bgcolor="#1A1A1A", plot_bgcolor="#1A1A1A",
            font=dict(family="Inter, system-ui", color="#ECECEC", size=12),
            title_font=dict(size=14, color="#ECECEC"),
            xaxis=dict(gridcolor="#2E2E2E", tickcolor="#8A8A8A",
                       tickfont=dict(color="#8A8A8A"), showgrid=False),
            yaxis=dict(gridcolor="#2E2E2E", tickcolor="#8A8A8A",
                       tickfont=dict(color="#8A8A8A"), gridwidth=1),
            showlegend=False,
            margin=dict(t=50, b=20, l=10, r=10),
        )
        fig_bar.update_traces(
            marker_color="#D97757", marker_line_color="#C06444",
            marker_line_width=1, textfont_color="#ECECEC", textposition="outside",
        )

        # Donut chart — clean vs exceptions
        fig_donut = go.Figure(data=[go.Pie(
            labels=["Clean", "Exceptions"],
            values=[clean, exc_n],
            hole=0.68,
            marker=dict(colors=["#2ECC71", "#D97757"],
                        line=dict(color="#1A1A1A", width=3)),
            textinfo="percent",
            textfont=dict(color="#ECECEC", size=12),
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        )])
        fig_donut.update_layout(
            paper_bgcolor="#1A1A1A", plot_bgcolor="#1A1A1A",
            font=dict(family="Inter, system-ui", color="#ECECEC"),
            title=dict(text="Clean vs Exceptions", font=dict(size=14, color="#ECECEC")),
            legend=dict(font=dict(color="#8A8A8A", size=12), bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=50, b=20, l=20, r=20),
            annotations=[dict(
                text=f"<b>{pct.split('%')[0]}%</b><br><span style='font-size:10px;color:#8A8A8A'>clean</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="#ECECEC", family="Inter"),
            )],
        )

        col_bar, col_donut = st.columns([3, 2], gap="large")
        with col_bar:
            st.plotly_chart(fig_bar,   use_container_width=True, config={"displayModeBar": False})
        with col_donut:
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    # ── Human review queue ────────────────────────────────────────────────────
    st.markdown('<div class="fo-section">Human Review Queue</div>', unsafe_allow_html=True)

    review_items = [inv for inv in invs if float(inv.get("confidence", 1.0)) < 0.8]

    if not review_items:
        st.markdown("""
        <div class="success-bar">
          All exceptions meet the 80% confidence threshold — no manual review required.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="color:#F39C12;font-size:13px;margin-bottom:1rem;font-weight:500;">
          {len(review_items)} exception(s) flagged for manual review
        </div>""", unsafe_allow_html=True)

        for inv in review_items:
            c = float(inv.get("confidence", 0))
            cbadge = _conf_badge(c)
            cases  = inv.get("similar_cases") or []
            cases_html = ""
            if cases:
                tags = "".join(f'<span class="ct">{escape(x)}</span>' for x in cases)
                cases_html = f'<div class="rv-cases">Similar cases: {tags}</div>'

            st.markdown(f"""
            <div class="rv-card">
              <div class="rv-hdr">
                <span class="badge b-orange">NEEDS REVIEW</span>
                <span class="rv-acct">{escape(str(inv["account"]))}</span>
                <span class="rv-meta">
                  {escape(str(inv["exception_type"]))} &nbsp;·&nbsp;
                  ${float(inv["variance"]):,.0f} USD
                </span>
                {cbadge}
              </div>
              <div class="rv-grid">
                <div>
                  <div class="rv-lbl">Root Cause</div>
                  <div class="rv-val">{escape(str(inv["root_cause"]))}</div>
                </div>
                <div>
                  <div class="rv-lbl">Recommended Action</div>
                  <div class="rv-val">{escape(str(inv["recommended_action"]))}</div>
                </div>
              </div>
              {cases_html}
            </div>""", unsafe_allow_html=True)

    # ── Export ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="fo-section">Export</div>', unsafe_allow_html=True)

    col_dl, col_rpt = st.columns([1, 2])
    with col_dl:
        if invs:
            st.download_button(
                "Download Exception Report (CSV)",
                data=pd.DataFrame(invs).to_csv(index=False).encode("utf-8"),
                file_name="finops_exception_report.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )
    with col_rpt:
        if state.get("report"):
            with st.expander("View full text report"):
                st.text(state["report"])

else:
    # ── Empty state ───────────────────────────────────────────────────────────
    if not st.session_state.run_error:
        st.markdown("""
        <div class="empty">
          <div class="empty-title">No reconciliation run yet</div>
          <div class="empty-sub">
            Load your GL Balances and Subledger CSVs using the sidebar,<br>
            or click <strong style="color:#D97757;">Use Sample Data</strong> to demo with 55 synthetic accounts.<br>
            Then click <strong style="color:#D97757;">Run Reconciliation</strong> to start the pipeline.
          </div>
        </div>""", unsafe_allow_html=True)
