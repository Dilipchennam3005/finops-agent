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
    initial_sidebar_state="collapsed",
)

# Minimal CSS — just hide chrome and style the two custom elements
st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}
.b-green  { background: rgba(46,204,113,0.15);  color: #2ECC71; }
.b-yellow { background: rgba(243,156,18,0.15);   color: #F39C12; }
.b-red    { background: rgba(231,76,60,0.15);    color: #E74C3C; }
.b-orange { background: rgba(217,119,87,0.15);   color: #D97757; }
.b-blue   { background: rgba(52,152,219,0.15);   color: #3498DB; }
.b-gray   { background: rgba(138,138,138,0.1);   color: #8A8A8A; }
.rv-card {
    border-left: 3px solid #D97757;
    background: #1A1A1A;
    border-radius: 6px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
}
.rv-label { font-size: 11px; font-weight: 600; color: #8A8A8A; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px; }
.rv-value { font-size: 13px; color: #ECECEC; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
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
    if c >= 0.8:  cls = "b-green"
    elif c >= 0.65: cls = "b-yellow"
    else: cls = "b-red"
    return f'<span class="badge {cls}">{c:.0%}</span>'


def _type_badge(t: str) -> str:
    cls = {"FX_DISCREPANCY": "b-yellow", "GL_MISMATCH": "b-red",
           "GL_ONLY": "b-orange", "SUBLEDGER_ONLY": "b-blue"}.get(t, "b-gray")
    return f'<span class="badge {cls}">{escape(t)}</span>'


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"gl_path": None, "sl_path": None, "using_sample": False,
              "run_complete": False, "run_error": None, "results": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar — settings only ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Settings")
    threshold = st.number_input(
        "Variance threshold (USD)",
        min_value=1_000, max_value=500_000, value=10_000, step=1_000,
        help="Flag exceptions above this amount",
    )
    st.divider()
    st.caption("LangGraph · ChromaDB · Claude")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("FinOps Agent")
st.caption("Financial Reconciliation Intelligence  ·  v0.5")
st.divider()

# ── Load Data ─────────────────────────────────────────────────────────────────
st.subheader("Load Data")

raw_dir = ROOT / "data" / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)

col_gl, col_sl, col_btn = st.columns([5, 5, 3], gap="large")

with col_gl:
    gl_file = st.file_uploader("GL Balances CSV", type="csv", key="gl_upload", on_change=_reset_run)

with col_sl:
    sl_file = st.file_uploader("Subledger CSV", type="csv", key="sl_upload", on_change=_reset_run)

with col_btn:
    st.write("")
    st.write("")
    if st.button("Use Sample Data", use_container_width=True):
        st.session_state.gl_path      = str(ROOT / "data" / "raw" / "gl_balances.csv")
        st.session_state.sl_path      = str(ROOT / "data" / "raw" / "subledger.csv")
        st.session_state.using_sample = True
        _reset_run()
        st.rerun()
    st.caption("55 synthetic accounts, 10 intentional mismatches")

if gl_file:
    p = raw_dir / "uploaded_gl.csv"
    p.write_bytes(gl_file.getvalue())
    st.session_state.gl_path = str(p)
    st.session_state.using_sample = False
    _reset_run()

if sl_file:
    p = raw_dir / "uploaded_sl.csv"
    p.write_bytes(sl_file.getvalue())
    st.session_state.sl_path = str(p)
    st.session_state.using_sample = False
    _reset_run()

# ── Run ───────────────────────────────────────────────────────────────────────
st.divider()
data_ready = bool(st.session_state.gl_path and st.session_state.sl_path)

col_run, col_status = st.columns([2, 5])
with col_run:
    run_clicked = st.button(
        "Run Reconciliation",
        type="primary",
        disabled=not data_ready,
        use_container_width=True,
    )
with col_status:
    if data_ready:
        src = "Sample data" if st.session_state.using_sample else "Uploaded files"
        st.success(f"{src} loaded — ready to run", icon="✓")
    else:
        missing = " and ".join(
            n for n, p in [("GL Balances", st.session_state.gl_path),
                           ("Subledger", st.session_state.sl_path)] if not p
        )
        st.info(f"Upload {missing}, or use sample data")

# ── Pipeline execution ────────────────────────────────────────────────────────
if run_clicked and data_ready:
    _reset_run()

    from agents.reconciliation_agent import run_matching_engine
    from agents.investigation_agent  import investigation_agent
    from agents.orchestrator import FinOpsState, reporting_agent, human_review_node

    state: FinOpsState = {
        "raw_data": {}, "exceptions": [], "investigations": [],
        "report": "", "confidence": 0.0, "human_review": False,
    }
    ok = True

    with st.status("Running pipeline...", expanded=True) as status:

        if _kb_count() == 0:
            status.write("Building knowledge base (first-run setup)...")
            try:
                _build_kb()
                status.write(f"  Knowledge base ready — {_kb_count()} records")
            except Exception as exc:
                status.write(f"  KB build failed: {type(exc).__name__}: {exc}")

        status.write("Agent 1 · Reconciliation — matching GL vs Subledger...")
        try:
            recon = run_matching_engine(
                gl_path=st.session_state.gl_path,
                subledger_path=st.session_state.sl_path,
                output_dir=str(ROOT / "data" / "processed"),
                threshold=float(threshold),
            )
            state["exceptions"] = recon["exceptions"]
            state["raw_data"] = {
                "total_accounts" : recon["total_accounts"],
                "matched_count"  : recon["matched_count"],
                "exception_count": recon["exception_count"],
                "threshold_usd"  : recon["threshold_usd"],
            }
            status.write(
                f"  {recon['matched_count']}/{recon['total_accounts']} matched — "
                f"{recon['exception_count']} exceptions above ${recon['threshold_usd']:,.0f}"
            )
        except Exception as exc:
            st.session_state.run_error = f"{type(exc).__name__}: {exc}"
            status.update(label="Reconciliation failed", state="error")
            ok = False

        if ok:
            status.write(f"Agent 2 · Investigation — analysing {len(state['exceptions'])} exceptions...")
            try:
                state = investigation_agent(state)
                status.write(
                    f"  Done — avg confidence {state['confidence']:.0%}"
                )
            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}"
                status.write(f"  Investigation unavailable — {err}")
                state["investigations"] = [
                    {"account": ex["account"], "exception_type": ex["type"],
                     "variance": ex["variance"], "currency": ex["currency"],
                     "root_cause": f"Unavailable: {err}",
                     "recommended_action": "Manual review required",
                     "confidence": 0.5, "exception_category": "OTHER", "similar_cases": []}
                    for ex in state["exceptions"]
                ]
                state["confidence"] = 0.5

        if ok:
            status.write("Agent 3 · Reporting...")
            state = human_review_node(state) if state["confidence"] < 0.8 else reporting_agent(state)
            status.update(label="Pipeline complete", state="complete")

    if ok:
        st.session_state.results      = state
        st.session_state.run_complete = True
        st.rerun()

if st.session_state.run_error:
    st.error(st.session_state.run_error)

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.run_complete and st.session_state.results:
    state = st.session_state.results
    raw   = state["raw_data"]
    invs  = state["investigations"]
    excs  = state["exceptions"]
    conf  = state["confidence"]

    st.divider()
    st.subheader("Results")

    # Summary metrics
    total = raw.get("total_accounts", 0)
    clean = raw.get("matched_count", 0)
    exc_n = raw.get("exception_count", 0)
    thr   = raw.get("threshold_usd", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accounts",        total)
    c2.metric("Clean Reconciliations", clean,  delta=f"{clean/total*100:.0f}% of total" if total else None, delta_color="off")
    c3.metric("Exceptions Found",      exc_n,  delta=f">${thr:,.0f} threshold", delta_color="off")
    c4.metric("Avg AI Confidence",     f"{conf:.0%}",
              delta="auto-approved" if conf >= 0.8 else "needs review",
              delta_color="normal" if conf >= 0.8 else "inverse")

    st.divider()

    # Exception details — collapsible table
    with st.expander("Exception Details", expanded=True):
        if invs:
            df = pd.DataFrame(invs)
            has_similar = any(
                isinstance(inv.get("similar_cases"), list) and inv["similar_cases"]
                for inv in invs
            )

            # Build rows HTML for the badges, keep rest as dataframe
            rows_html = ""
            for inv in invs:
                sim = ", ".join(inv.get("similar_cases") or []) or "—"
                rows_html += f"""<tr>
                  <td style="padding:10px 12px;color:#ECECEC;font-family:monospace;font-size:13px;">{escape(str(inv['account']))}</td>
                  <td style="padding:10px 12px;">{_type_badge(inv['exception_type'])}</td>
                  <td style="padding:10px 12px;color:#ECECEC;font-family:monospace;">${float(inv['variance']):,.0f}</td>
                  <td style="padding:10px 12px;color:#8A8A8A;font-size:12px;">{escape(inv['currency'])}</td>
                  <td style="padding:10px 12px;color:#ECECEC;font-size:12px;max-width:280px;line-height:1.5;">{escape(str(inv['root_cause']))}</td>
                  <td style="padding:10px 12px;color:#ECECEC;font-size:12px;max-width:240px;line-height:1.5;">{escape(str(inv['recommended_action']))}</td>
                  <td style="padding:10px 12px;">{_conf_badge(float(inv['confidence']))}</td>
                  {"<td style='padding:10px 12px;color:#8A8A8A;font-size:11px;font-family:monospace;'>" + escape(sim) + "</td>" if has_similar else ""}
                </tr>"""

            sim_th = "<th style='padding:10px 12px;'>Similar Cases</th>" if has_similar else ""
            th_style = "padding:10px 12px;text-align:left;font-size:11px;font-weight:600;color:#D97757;text-transform:uppercase;letter-spacing:0.05em;border-bottom:1px solid #2E2E2E;"

            st.markdown(f"""
            <div style="overflow-x:auto;border:1px solid #2E2E2E;border-radius:8px;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <thead style="background:#111;">
                <tr>
                  <th style="{th_style}">Account</th>
                  <th style="{th_style}">Type</th>
                  <th style="{th_style}">Variance</th>
                  <th style="{th_style}">Currency</th>
                  <th style="{th_style}">Root Cause</th>
                  <th style="{th_style}">Recommended Action</th>
                  <th style="{th_style}">Confidence</th>
                  {sim_th}
                </tr>
              </thead>
              <tbody>{"".join(rows_html.split())}</tbody>
            </table>
            </div>
            """, unsafe_allow_html=True)

    # Analytics — bar + donut
    with st.expander("Analytics", expanded=False):
        if excs:
            type_df = (
                pd.DataFrame(excs).groupby("type").size()
                .reset_index(name="Count").rename(columns={"type": "Type"})
            )

            fig_bar = px.bar(
                type_df, x="Type", y="Count", text="Count",
                color_discrete_sequence=["#D97757"],
                title="Exceptions by Type",
            )
            fig_bar.update_layout(
                paper_bgcolor="#1A1A1A", plot_bgcolor="#1A1A1A",
                font=dict(color="#ECECEC", size=12),
                title_font_size=14,
                xaxis=dict(showgrid=False, tickfont=dict(color="#8A8A8A")),
                yaxis=dict(gridcolor="#2E2E2E", tickfont=dict(color="#8A8A8A")),
                showlegend=False, margin=dict(t=40, b=20, l=10, r=10),
            )
            fig_bar.update_traces(textposition="outside", textfont_color="#ECECEC",
                                  marker_line_width=0)

            fig_donut = go.Figure(go.Pie(
                labels=["Clean", "Exceptions"],
                values=[clean, exc_n],
                hole=0.65,
                marker=dict(colors=["#2ECC71", "#D97757"],
                            line=dict(color="#1A1A1A", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#ECECEC", size=12),
                hovertemplate="%{label}: %{value}<extra></extra>",
            ))
            fig_donut.update_layout(
                title="Clean vs Exceptions",
                paper_bgcolor="#1A1A1A",
                font=dict(color="#ECECEC"),
                title_font_size=14,
                showlegend=False,
                margin=dict(t=40, b=20, l=20, r=20),
                annotations=[dict(
                    text=f"<b>{clean/total*100:.0f}%</b><br>clean" if total else "",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=18, color="#ECECEC"),
                )],
            )

            col_a, col_b = st.columns([3, 2])
            with col_a:
                st.plotly_chart(fig_bar,   use_container_width=True, config={"displayModeBar": False})
            with col_b:
                st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    # Human review queue
    review_items = [inv for inv in invs if float(inv.get("confidence", 1.0)) < 0.8]
    review_label = f"Human Review Queue  ·  {len(review_items)} flagged" if review_items else "Human Review Queue  ·  none required"

    with st.expander(review_label, expanded=bool(review_items)):
        if not review_items:
            st.success("All exceptions above the 80% confidence threshold.")
        else:
            for inv in review_items:
                c = float(inv.get("confidence", 0))
                cases = inv.get("similar_cases") or []
                cases_str = "  ·  Similar: " + ", ".join(cases) if cases else ""
                st.markdown(f"""
                <div class="rv-card">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.75rem;flex-wrap:wrap;">
                    <span class="badge b-orange">NEEDS REVIEW</span>
                    <span style="font-weight:600;font-family:monospace;">{escape(str(inv['account']))}</span>
                    <span style="color:#8A8A8A;font-size:12px;">{escape(inv['exception_type'])}  ·  ${float(inv['variance']):,.0f} USD  ·  {c:.0%} confidence{escape(cases_str)}</span>
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
                    <div>
                      <div class="rv-label">Root Cause</div>
                      <div class="rv-value">{escape(str(inv['root_cause']))}</div>
                    </div>
                    <div>
                      <div class="rv-label">Recommended Action</div>
                      <div class="rv-value">{escape(str(inv['recommended_action']))}</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # Export
    st.divider()
    col_dl, _ = st.columns([1, 3])
    with col_dl:
        st.download_button(
            "Download Exception Report (CSV)",
            data=pd.DataFrame(invs).to_csv(index=False).encode("utf-8"),
            file_name="finops_exception_report.csv",
            mime="text/csv",
            use_container_width=True,
        )
