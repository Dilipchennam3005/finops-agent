"""
Reconciliation Agent — v0.3

Reads GL and subledger CSVs, matches on (account_code, currency, period, entity),
applies FX conversion to USD, calculates variance, and flags exceptions above threshold.

Outputs:
  data/processed/reconciled_clean.csv   — matched records within threshold
  data/processed/exceptions.csv         — flagged records requiring investigation
"""
import os
from pathlib import Path

import pandas as pd

# FX conversion rates: local currency → USD
FX_RATES: dict[str, float] = {
    "USD": 1.00,
    "GBP": 1.27,
    "EUR": 1.08,
}

VARIANCE_THRESHOLD: float = 10_000.0  # USD


def run_matching_engine(
    gl_path: str,
    subledger_path: str,
    output_dir: str,
    threshold: float = VARIANCE_THRESHOLD,
    fx_rates: dict[str, float] | None = None,
) -> dict:
    """
    Core matching engine. Returns a summary dict containing:
      - exceptions:       list of exception dicts ready for the LangGraph state
      - total_accounts:   total rows after outer-join
      - matched_count:    rows within threshold
      - exception_count:  rows exceeding threshold or unmatched
      - threshold_usd:    the effective threshold used
    """
    if fx_rates is None:
        fx_rates = FX_RATES

    gl = pd.read_csv(gl_path)
    sl = pd.read_csv(subledger_path)

    # Outer-join so GL-only and subledger-only rows both surface
    merged = pd.merge(
        gl,
        sl[["account_code", "currency", "subledger_balance", "period", "entity"]],
        on=["account_code", "currency", "period", "entity"],
        how="outer",
        indicator=True,
    )

    # Fill missing balances with 0 (one side is absent for GL_ONLY / SUBLEDGER_ONLY)
    merged["gl_balance"] = merged["gl_balance"].fillna(0.0)
    merged["subledger_balance"] = merged["subledger_balance"].fillna(0.0)

    # FX conversion to USD
    merged["fx_rate"] = merged["currency"].map(fx_rates).fillna(1.0)
    merged["gl_balance_usd"] = merged["gl_balance"] * merged["fx_rate"]
    merged["subledger_balance_usd"] = merged["subledger_balance"] * merged["fx_rate"]
    merged["variance_usd"] = merged["gl_balance_usd"] - merged["subledger_balance_usd"]

    # Classify each row
    def _classify(row: pd.Series) -> str:
        if row["_merge"] == "left_only":
            return "GL_ONLY"
        if row["_merge"] == "right_only":
            return "SUBLEDGER_ONLY"
        if abs(row["variance_usd"]) > threshold:
            return "FX_DISCREPANCY" if row["currency"] != "USD" else "GL_MISMATCH"
        return "MATCHED"

    merged["exception_type"] = merged.apply(_classify, axis=1)
    merged.drop(columns=["_merge"], inplace=True)

    clean = merged[merged["exception_type"] == "MATCHED"].copy()
    exceptions = merged[merged["exception_type"] != "MATCHED"].copy()

    # Write outputs
    os.makedirs(output_dir, exist_ok=True)
    clean.to_csv(os.path.join(output_dir, "reconciled_clean.csv"), index=False)
    exceptions.to_csv(os.path.join(output_dir, "exceptions.csv"), index=False)

    # Build the exceptions list consumed by downstream agents
    exception_list = [
        {
            "account": row["account_code"],
            "variance": round(row["variance_usd"], 2),
            "currency": row["currency"],
            "source_a": round(row["gl_balance_usd"], 2),
            "source_b": round(row["subledger_balance_usd"], 2),
            "type": row["exception_type"],
            "entity": row.get("entity", ""),
        }
        for _, row in exceptions.iterrows()
    ]

    return {
        "exceptions": exception_list,
        "total_accounts": len(merged),
        "matched_count": len(clean),
        "exception_count": len(exceptions),
        "threshold_usd": threshold,
    }


def reconciliation_agent(state: dict) -> dict:
    """LangGraph node: runs the matching engine and writes results into shared state."""
    print("Agent 1: Reconciliation Agent running...")

    base = Path(__file__).parent.parent
    gl_path = str(base / "data" / "raw" / "gl_balances.csv")
    sl_path = str(base / "data" / "raw" / "subledger.csv")
    output_dir = str(base / "data" / "processed")

    result = run_matching_engine(gl_path, sl_path, output_dir)

    state["exceptions"] = result["exceptions"]
    state["raw_data"] = {
        "total_accounts": result["total_accounts"],
        "matched_count": result["matched_count"],
        "exception_count": result["exception_count"],
        "threshold_usd": result["threshold_usd"],
        "gl_path": gl_path,
        "subledger_path": sl_path,
        "clean_output": os.path.join(output_dir, "reconciled_clean.csv"),
        "exceptions_output": os.path.join(output_dir, "exceptions.csv"),
    }

    print(
        f"  Matched {result['matched_count']}/{result['total_accounts']} accounts — "
        f"{result['exception_count']} exceptions above ${result['threshold_usd']:,.0f} USD threshold"
    )
    return state
