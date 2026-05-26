# finops-agent

# FinOps Agent 🤖

> A multi-agent AI system for financial operations — automating 
> reconciliation, exception investigation, and reporting using 
> LangGraph, RAG, dbt, DuckDB, and Streamlit.

---

## Why I Built This

Most finance teams still reconcile in Excel. Month-end close takes 
days of manual work across multiple systems. I spent 4 years building 
automated reconciliation systems in production at State Street and 
Mphasis — this project reimagines that work as an intelligent 
multi-agent AI system accessible to any finance team.

---

## Architecture

Raw Data (CSV/Excel)
↓
dbt + DuckDB (data modelling & transformation)
↓
┌──────────────────────────────────────────┐
│          LangGraph Orchestrator          │
│                                          │
│  Agent 1: Reconciliation Agent           │
│  → Ingests data, runs matching logic,    │
│    identifies exceptions & variances     │
│                                          │
│  Agent 2: Investigation Agent (RAG)      │
│  → Retrieves similar past exceptions     │
│    from ChromaDB, analyses root cause    │
│                                          │
│  Agent 3: Reporting Agent                │
│  → Generates structured exception        │
│    report with recommendations           │
│                                          │
│  Human Review Node                       │
│  → Low-confidence exceptions routed      │
│    for manual approval                   │
└──────────────────────────────────────────┘
↓
Streamlit Dashboard (results + insights)


---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Agent Orchestration | LangGraph |
| LLM | Claude (Anthropic) |
| RAG / Vector Store | ChromaDB |
| Data Transformation | dbt + DuckDB |
| Data Processing | Python, pandas |
| Frontend | Streamlit + Plotly |
| Version Control | Git |

---

## Version History

### v0.1 — Environment Setup & Project Scaffold ✅
- Initialized project structure
- Configured virtual environment
- Installed all dependencies
- README established

### v0.2 — Agent Skeleton & LangGraph Orchestration ✅
- Three agents communicating via LangGraph
- State passing between agents
- Sample data ingestion

### v0.3 — Reconciliation Engine ✅
- Real matching engine in `agents/reconciliation_agent.py` — replaces placeholder
- Reads `data/raw/gl_balances.csv` and `data/raw/subledger.csv`
- Matches records on `(account_code, currency, period, entity)`
- Applies FX conversion (GBP → USD at 1.27, EUR → USD at 1.08) before comparing
- Flags `GL_MISMATCH`, `FX_DISCREPANCY`, `GL_ONLY`, and `SUBLEDGER_ONLY` exceptions
- Configurable variance threshold (default $10,000 USD)
- Writes `data/processed/reconciled_clean.csv` and `data/processed/exceptions.csv`
- Orchestrator now passes real exception data to the investigation agent
- Synthetic test data: 55 accounts (30 USD / 15 GBP / 10 EUR), 10 intentional mismatches built in
- Generator script: `python data/generate_sample_data.py`

### v0.4 — RAG Investigation Layer ✅
- `data/build_knowledge_base.py` — 32 synthetic historical exception records across 6 categories (FX_TIMING, GL_CODING_ERROR, INTERCOMPANY, PERIOD_CUTOFF, SYSTEM_ERROR, MANUAL_JOURNAL)
- ChromaDB PersistentClient in `data/vector_store/` with cosine-distance HNSW index (all-MiniLM-L6-v2 embeddings via ONNX)
- `agents/investigation_agent.py` — for each exception: queries ChromaDB top-3 similar historical cases, calls Claude API (`claude-haiku-4-5`) with structured-output JSON schema
- Claude returns: `root_cause`, `recommended_action`, `confidence` (0–1), `exception_category`
- Confidence routing: average ≥ 0.80 → reporting agent; < 0.80 → human review node (generates flagged report)
- System prompt cached via `cache_control: ephemeral` to minimise API cost across all 10 per-run calls
- Reporting agent updated to include category, root cause, recommended action, similar case IDs

### v0.5 — dbt + DuckDB Integration ⏳
- Raw data modelled through dbt staging and mart layers
- DuckDB as local warehouse
- Incremental loading logic

### v0.6 — Human Review Node ⏳
- Low confidence exceptions routed for manual approval
- Audit trail logging

### v0.7 — Streamlit Dashboard ⏳
- Upload CSVs, run reconciliation, see results
- Exception investigation view
- Plotly charts for variance analysis

### v1.0 — Production Ready ⏳
- Clean packaging
- Full documentation
- pip installable
- Sample data included

---

## Getting Started

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/finops-agent.git
cd finops-agent

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your API key
# Edit .env and add: ANTHROPIC_API_KEY=your_key_here

# Run the app (available from v0.7)
streamlit run streamlit_app/app.py
```

---

## Project Status

🚧 **Actively in development — building in public**

---

## Author

Dilip Kumar Chennam
[LinkedIn](https://linkedin.com/in/DilipChennam) | [GitHub](https://github.com/DilipChennam)
