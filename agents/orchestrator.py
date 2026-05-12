from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import os

load_dotenv()

# This is the shared state that all three agents read from and write to
class FinOpsState(TypedDict):
    raw_data: dict          # input data from CSV/Excel
    exceptions: list        # exceptions found by reconciliation agent
    investigations: list    # investigation results from RAG agent
    report: str             # final report from reporting agent
    confidence: float       # confidence score — low score routes to human review
    human_review: bool      # flag for human review needed

# Agent 1 — Reconciliation Agent
def reconciliation_agent(state: FinOpsState) -> FinOpsState:
    print("Agent 1: Reconciliation Agent running...")
    # Placeholder logic for now — we will replace this in v0.3
    state["exceptions"] = [
        {
            "account": "4210-APAC",
            "variance": 23400,
            "currency": "USD",
            "source_a": 150000,
            "source_b": 126600,
            "type": "GL_MISMATCH"
        },
        {
            "account": "3301-EMEA",
            "variance": 5200,
            "currency": "USD",
            "source_a": 98000,
            "source_b": 92800,
            "type": "FX_DISCREPANCY"
        }
    ]
    print(f"  Found {len(state['exceptions'])} exceptions")
    return state

# Agent 2 — Investigation Agent
def investigation_agent(state: FinOpsState) -> FinOpsState:
    print("Agent 2: Investigation Agent running...")
    # Placeholder logic for now — RAG layer comes in v0.4
    investigations = []
    for exception in state["exceptions"]:
        investigations.append({
            "account": exception["account"],
            "likely_cause": f"Variance of ${exception['variance']:,} flagged for {exception['type']}. Full AI investigation coming in v0.4.",
            "confidence": 0.75
        })
    state["investigations"] = investigations
    state["confidence"] = 0.75
    print(f"  Investigated {len(investigations)} exceptions")
    return state

# Agent 3 — Reporting Agent
def reporting_agent(state: FinOpsState) -> FinOpsState:
    print("Agent 3: Reporting Agent running...")
    lines = ["=== FINOPS EXCEPTION REPORT ===\n"]
    for inv in state["investigations"]:
        lines.append(f"Account: {inv['account']}")
        lines.append(f"Finding: {inv['likely_cause']}")
        lines.append(f"Confidence: {inv['confidence']}\n")
    state["report"] = "\n".join(lines)
    print("  Report generated")
    return state

# Human Review Node
def human_review_node(state: FinOpsState) -> FinOpsState:
    print("⚠️  Low confidence detected — routing to human review")
    state["human_review"] = True
    return state

# Router — decides whether to go to reporting or human review
def route_after_investigation(state: FinOpsState) -> str:
    if state["confidence"] < 0.7:
        return "human_review"
    return "reporting_agent"

# Build the graph
def build_graph():
    graph = StateGraph(FinOpsState)

    # Add all nodes
    graph.add_node("reconciliation_agent", reconciliation_agent)
    graph.add_node("investigation_agent", investigation_agent)
    graph.add_node("reporting_agent", reporting_agent)
    graph.add_node("human_review", human_review_node)

    # Define the flow
    graph.set_entry_point("reconciliation_agent")
    graph.add_edge("reconciliation_agent", "investigation_agent")
    graph.add_conditional_edges(
        "investigation_agent",
        route_after_investigation,
        {
            "reporting_agent": "reporting_agent",
            "human_review": "human_review"
        }
    )
    graph.add_edge("reporting_agent", END)
    graph.add_edge("human_review", END)

    return graph.compile()

if __name__ == "__main__":
    graph = build_graph()
    
    # Initial state
    initial_state: FinOpsState = {
        "raw_data": {},
        "exceptions": [],
        "investigations": [],
        "report": "",
        "confidence": 0.0,
        "human_review": False
    }

    print("\n🚀 Running FinOps Agent...\n")
    result = graph.invoke(initial_state)
    print("\n📋 FINAL REPORT:")
    print(result["report"])