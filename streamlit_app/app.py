"""
FinOps Agent — Streamlit Frontend (v0.5)
Run: streamlit run streamlit_app/app.py
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinOps Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 100%);
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {
    color: #c8c8f0 !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background-color: #3a3a8f;
    color: #ffffff !important;
    border: 1px solid #5555bb;
    border-radius: 6px;
    width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #5050bb;
}
section[data-testid="stSidebar"] .stNumberInput input {
    background-color: #1e1e4a;
    color: #e0e0ff;
    border-color: #3a3a8f;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## FinOps Agent")
    st.markdown("**v0.5**  ·  AI-powered reconciliation")
    st.divider()

    st.markdown("### Pipeline")
    st.markdown("""
1. **Reconciliation** — GL vs Subledger
2. **Investigation** — RAG + Claude
3. **Reporting** — Exception report
    """)
    st.divider()

    st.markdown("### Settings")
    threshold = st.number_input(
        "Variance threshold (USD)",
        min_value=1_000,
        max_value=500_000,
        value=10_000,
        step=1_000,
        help="Exceptions above this amount in USD are flagged",
    )
    st.divider()
    st.caption("LangGraph · ChromaDB · Claude API")
    st.caption("github.com/Dilipchennam3005/finops-agent")

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "gl_path": None,
    "sl_path": None,
    "using_sample": False,
    "run_complete": False,
    "run_error": None,
    "results": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def _reset_run():
    st.session_state.run_complete = False
    st.session_state.run_error = None
    st.session_state.results = None


# ── Knowledge base helper ─────────────────────────────────────────────────────
VECTOR_STORE_PATH = str(ROOT / "data" / "vector_store")
KB_COLLECTION = "finops_exceptions"


def _kb_count() -> int:
    """Return number of documents in the ChromaDB collection, or 0 if missing."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
        return client.get_collection(KB_COLLECTION).count()
    except Exception:
        return 0


def _build_kb() -> None:
    """Dynamically import and run data/build_knowledge_base.py's build()."""
    spec = importlib.util.spec_from_file_location(
        "build_knowledge_base", ROOT / "data" / "build_knowledge_base.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.build(VECTOR_STORE_PATH)


# ── Header ────────────────────────────────────────────────────────────────────
st.title("FinOps Agent")
st.markdown(
    "Automated GL / Subledger reconciliation with AI-powered exception investigation "
    "using ChromaDB RAG + Claude."
)

# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load data
# ════════════════════════════════════════════════════════════════════════════
st.header("1  ·  Load Data")

left, right = st.columns([3, 1], gap="large")

with left:
    col_gl, col_sl = st.columns(2)
    with col_gl:
        gl_file = st.file_uploader(
            "GL Balances CSV",
            type="csv",
            key="gl_upload",
            on_change=_reset_run,
        )
    with col_sl:
        sl_file = st.file_uploader(
            "Subledger CSV",
            type="csv",
            key="sl_upload",
            on_change=_reset_run,
        )

with right:
    st.markdown("**No files?**")
    st.markdown("Load the built-in 55-account synthetic dataset to demo the pipeline instantly.")
    if st.button("Use Sample Data", use_container_width=True):
        st.session_state.gl_path = str(ROOT / "data" / "raw" / "gl_balances.csv")
        st.session_state.sl_path = str(ROOT / "data" / "raw" / "subledger.csv")
        st.session_state.using_sample = True
        _reset_run()
        st.rerun()

# Handle uploads — persist to data/raw/
raw_dir = ROOT / "data" / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)

if gl_file is not None:
    dest = raw_dir / "uploaded_gl.csv"
    dest.write_bytes(gl_file.getvalue())
    st.session_state.gl_path = str(dest)
    st.session_state.using_sample = False
    _reset_run()

if sl_file is not None:
    dest = raw_dir / "uploaded_sl.csv"
    dest.write_bytes(sl_file.getvalue())
    st.session_state.sl_path = str(dest)
    st.session_state.using_sample = False
    _reset_run()

# Status banner
if st.session_state.gl_path and st.session_state.sl_path:
    source = "sample data (55 synthetic accounts)" if st.session_state.using_sample else "uploaded files"
    st.success(f"Data loaded from {source}. Ready to run.")
else:
    missing = [
        name
        for name, path in [
            ("GL Balances", st.session_state.gl_path),
            ("Subledger", st.session_state.sl_path),
        ]
        if not path
    ]
    st.info(f"Upload {' and '.join(missing)}, or click **Use Sample Data**.")

# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Run pipeline
# ════════════════════════════════════════════════════════════════════════════
st.header("2  ·  Run Pipeline")

data_ready = bool(st.session_state.gl_path and st.session_state.sl_path)

if st.button("Run Reconciliation", type="primary", disabled=not data_ready):
    _reset_run()

    from agents.reconciliation_agent import run_matching_engine
    from agents.investigation_agent import investigation_agent
    from agents.orchestrator import FinOpsState, reporting_agent, human_review_node

    output_dir = str(ROOT / "data" / "processed")

    state: FinOpsState = {
        "raw_data": {},
        "exceptions": [],
        "investigations": [],
        "report": "",
        "confidence": 0.0,
        "human_review": False,
    }

    pipeline_ok = True

    with st.status("Running FinOps pipeline...", expanded=True) as status:

        # ── Knowledge base check ──────────────────────────────────────────
        if _kb_count() == 0:
            status.write("**Building knowledge base** — first-run setup (32 historical records)...")
            try:
                _build_kb()
                status.write(f"  Knowledge base ready ({_kb_count()} records)")
            except Exception as exc:
                status.write(f"  Knowledge base build failed: {type(exc).__name__}: {exc}")

        # ── Agent 1: Reconciliation ───────────────────────────────────────
        status.write("**Agent 1 · Reconciliation** — matching GL vs Subledger...")
        try:
            recon = run_matching_engine(
                gl_path=st.session_state.gl_path,
                subledger_path=st.session_state.sl_path,
                output_dir=output_dir,
                threshold=float(threshold),
            )
            state["exceptions"] = recon["exceptions"]
            state["raw_data"] = {
                "total_accounts": recon["total_accounts"],
                "matched_count": recon["matched_count"],
                "exception_count": recon["exception_count"],
                "threshold_usd": recon["threshold_usd"],
                "clean_output": output_dir + "/reconciled_clean.csv",
                "exceptions_output": output_dir + "/exceptions.csv",
            }
            status.write(
                f"  Matched **{recon['matched_count']}/{recon['total_accounts']}** accounts — "
                f"**{recon['exception_count']}** exceptions above ${recon['threshold_usd']:,.0f}"
            )
        except Exception as exc:
            st.session_state.run_error = f"Reconciliation failed: {type(exc).__name__}: {exc}"
            status.update(label="Pipeline failed at reconciliation", state="error")
            pipeline_ok = False

        # ── Agent 2: Investigation ─────────────────────────────────────────
        if pipeline_ok:
            status.write(
                f"**Agent 2 · Investigation** — analysing {len(state['exceptions'])} exceptions "
                "with RAG + Claude..."
            )
            try:
                state = investigation_agent(state)
                status.write(
                    f"  Investigated **{len(state['investigations'])}** exceptions — "
                    f"avg confidence **{state['confidence']:.0%}**"
                )
            except Exception as exc:
                error_detail = f"{type(exc).__name__}: {exc}"
                status.write(f"  Investigation unavailable — {error_detail}")
                state["investigations"] = [
                    {
                        "account": ex["account"],
                        "exception_type": ex["type"],
                        "variance": ex["variance"],
                        "currency": ex["currency"],
                        "root_cause": f"Investigation unavailable: {error_detail}",
                        "recommended_action": "Manual review required",
                        "confidence": 0.5,
                        "exception_category": "OTHER",
                        "similar_cases": [],
                    }
                    for ex in state["exceptions"]
                ]
                state["confidence"] = 0.5

        # ── Agent 3: Reporting ─────────────────────────────────────────────
        if pipeline_ok:
            status.write("**Agent 3 · Reporting** — generating exception report...")
            if state["confidence"] < 0.8:
                state = human_review_node(state)
            else:
                state = reporting_agent(state)
            status.write("  Report generated")
            status.update(label="Pipeline complete", state="complete")

    if pipeline_ok:
        st.session_state.results = state
        st.session_state.run_complete = True
        st.rerun()

if st.session_state.run_error:
    st.error(st.session_state.run_error)

# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Results
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.run_complete and st.session_state.results:
    state = st.session_state.results
    raw = state["raw_data"]
    invs = state["investigations"]
    excs = state["exceptions"]

    st.header("3  ·  Results")

    # ── Summary cards ─────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accounts", raw.get("total_accounts", 0))
    c2.metric("Clean Reconciliations", raw.get("matched_count", 0))
    c3.metric(
        "Exceptions Found",
        raw.get("exception_count", 0),
        delta=f">${raw.get('threshold_usd', 0):,.0f} threshold",
        delta_color="off",
    )
    c4.metric(
        "Avg Confidence",
        f"{state['confidence']:.0%}",
        delta="needs review" if state["confidence"] < 0.8 else "auto-approved",
        delta_color="inverse" if state["confidence"] < 0.8 else "normal",
    )

    st.divider()

    # ── Exceptions table ──────────────────────────────────────────────────
    st.subheader("Exception Details")

    if invs:
        df = pd.DataFrame(invs)

        # Determine whether any similar_cases are populated
        has_similar = any(
            isinstance(inv.get("similar_cases"), list) and len(inv["similar_cases"]) > 0
            for inv in invs
        )

        df_disp = pd.DataFrame({
            "Account": df["account"],
            "Exception Type": df["exception_type"],
            "Currency": df["currency"],
            "Variance (USD)": df["variance"].astype(float),
            "Category": df["exception_category"],
            "Root Cause": df["root_cause"],
            "Recommended Action": df["recommended_action"],
            # ProgressColumn expects 0–100
            "Confidence": df["confidence"].astype(float) * 100,
        })

        if has_similar:
            df_disp["Similar Cases"] = df["similar_cases"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else ""
            )

        col_cfg = {
            "Account": st.column_config.TextColumn("Account", width="small"),
            "Exception Type": st.column_config.TextColumn("Exception Type", width="small"),
            "Currency": st.column_config.TextColumn("Currency", width="small"),
            "Variance (USD)": st.column_config.NumberColumn(
                "Variance (USD)",
                format="$ %.0f",
                width="small",
            ),
            "Category": st.column_config.TextColumn("AI Category", width="small"),
            "Root Cause": st.column_config.TextColumn("Root Cause", width="large"),
            "Recommended Action": st.column_config.TextColumn("Recommended Action", width="large"),
            "Confidence": st.column_config.ProgressColumn(
                "Confidence",
                min_value=0,
                max_value=100,
                format="%.0f%%",
                width="small",
            ),
        }
        if has_similar:
            col_cfg["Similar Cases"] = st.column_config.TextColumn(
                "Similar Cases", width="medium"
            )

        st.dataframe(
            df_disp,
            column_config=col_cfg,
            use_container_width=True,
            hide_index=True,
        )

    # ── Bar chart ──────────────────────────────────────────────────────────
    st.subheader("Exception Breakdown by Type")

    if excs:
        type_df = (
            pd.DataFrame(excs)
            .groupby("type")
            .size()
            .reset_index(name="Count")
            .rename(columns={"type": "Exception Type"})
        )
        color_map = {
            "GL_MISMATCH": "#e74c3c",
            "FX_DISCREPANCY": "#f39c12",
            "GL_ONLY": "#8e44ad",
            "SUBLEDGER_ONLY": "#2980b9",
        }
        fig = px.bar(
            type_df,
            x="Exception Type",
            y="Count",
            color="Exception Type",
            color_discrete_map=color_map,
            text="Count",
            title="Exceptions by Type",
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Arial", size=13),
            title_font_size=16,
            margin=dict(t=50, b=40),
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # ── Human review queue ────────────────────────────────────────────────
    review_items = [inv for inv in invs if inv.get("confidence", 1.0) < 0.8]

    st.subheader("Human Review Queue")
    if review_items:
        st.warning(
            f"{len(review_items)} exception(s) flagged for human review (confidence < 80%)"
        )
        for inv in review_items:
            conf = inv.get("confidence", 0)
            label = (
                f"[NEEDS REVIEW]  {inv['account']}  ·  "
                f"{inv['exception_type']}  ·  "
                f"${float(inv['variance']):,.0f} USD  ·  "
                f"{conf:.0%} confidence"
            )
            with st.expander(label):
                col_a, col_b = st.columns(2)
                col_a.markdown(f"**Root cause**  \n{inv['root_cause']}")
                col_b.markdown(f"**Recommended action**  \n{inv['recommended_action']}")
                st.markdown(f"**Category:** `{inv['exception_category']}`")
                if inv.get("similar_cases"):
                    st.markdown(
                        f"**Similar historical cases:** {', '.join(inv['similar_cases'])}"
                    )
    else:
        st.success(
            "All exceptions meet the 80% confidence threshold. No manual review required."
        )

    st.divider()

    # ── Export ────────────────────────────────────────────────────────────
    st.subheader("Export")
    col_dl, col_report = st.columns([1, 2])

    with col_dl:
        if invs:
            csv = pd.DataFrame(invs).to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Exception Report (CSV)",
                data=csv,
                file_name="finops_exception_report.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

    with col_report:
        if state.get("report"):
            with st.expander("View full text report"):
                st.text(state["report"])
