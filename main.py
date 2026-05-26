"""
Entry point — run the full FinOps agent pipeline.

Usage:
    python main.py
"""
from agents.orchestrator import build_graph, FinOpsState


def main() -> None:
    graph = build_graph()

    initial_state: FinOpsState = {
        "raw_data": {},
        "exceptions": [],
        "investigations": [],
        "report": "",
        "confidence": 0.0,
        "human_review": False,
    }

    print("\nRunning FinOps Agent...\n")
    result = graph.invoke(initial_state)

    raw = result.get("raw_data", {})
    if raw:
        print(f"\nReconciliation summary:")
        print(f"  Total accounts : {raw.get('total_accounts', '?')}")
        print(f"  Matched (clean): {raw.get('matched_count', '?')}")
        print(f"  Exceptions     : {raw.get('exception_count', '?')}")
        print(f"  Threshold (USD): ${raw.get('threshold_usd', 10000):,.0f}")
        print(f"  Clean output   : {raw.get('clean_output', '')}")
        print(f"  Exceptions out : {raw.get('exceptions_output', '')}")

    print("\nFINAL REPORT:")
    print(result["report"])


if __name__ == "__main__":
    main()
