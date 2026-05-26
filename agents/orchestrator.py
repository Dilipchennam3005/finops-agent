from typing import TypedDict
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from .reconciliation_agent import reconciliation_agent
from .investigation_agent import investigation_agent

load_dotenv()

# This is the shared state that all three agents read from and write to
class FinOpsState(TypedDict):
    raw_data: dict          # summary stats populated by reconciliation agent
    exceptions: list        # exceptions found by reconciliation agent
    investigations: list    # investigation results from RAG agent
    report: str             # final report from reporting agent
    confidence: float       # confidence score — low score routes to human review
    human_review: bool      # flag for human review needed

# Agent 3 — Reporting Agent
def reporting_agent(state: FinOpsState) -> FinOpsState:
    print("Agent 3: Reporting Agent running...")
    lines = ["=== FINOPS EXCEPTION REPORT ===\n"]
    for inv in state["investigations"]:
        lines.append(f"Account         : {inv['account']}")
        lines.append(f"Exception type  : {inv['exception_type']}")
        lines.append(f"Variance (USD)  : ${inv['variance']:,.2f}")
        lines.append(f"Category        : {inv['exception_category']}")
        lines.append(f"Root cause      : {inv['root_cause']}")
        lines.append(f"Recommended action: {inv['recommended_action']}")
        lines.append(f"Confidence      : {inv['confidence']:.0%}")
        lines.append(f"Similar cases   : {', '.join(inv['similar_cases'])}")
        lines.append("")
    state["report"] = "\n".join(lines)
    print("  Report generated")
    return state

# Human Review Node
def human_review_node(state: FinOpsState) -> FinOpsState:
    print("WARNING: Low confidence detected - routing to human review")
    state["human_review"] = True
    lines = [
        "=== FINOPS EXCEPTION REPORT — HUMAN REVIEW REQUIRED ===\n",
        f"Average confidence {state['confidence']:.0%} is below the 80% threshold.\n",
        "The following exceptions require manual review before sign-off:\n",
    ]
    for inv in state["investigations"]:
        flag = " [REVIEW]" if inv["confidence"] < 0.8 else ""
        lines.append(f"Account         : {inv['account']}{flag}")
        lines.append(f"Exception type  : {inv['exception_type']}")
        lines.append(f"Variance (USD)  : ${inv['variance']:,.2f}")
        lines.append(f"Category        : {inv['exception_category']}")
        lines.append(f"Root cause      : {inv['root_cause']}")
        lines.append(f"Recommended action: {inv['recommended_action']}")
        lines.append(f"Confidence      : {inv['confidence']:.0%}")
        lines.append(f"Similar cases   : {', '.join(inv['similar_cases'])}")
        lines.append("")
    state["report"] = "\n".join(lines)
    return state

# Router — decides whether to go to reporting or human review
def route_after_investigation(state: FinOpsState) -> str:
    if state["confidence"] < 0.8:
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

    print("\nRunning FinOps Agent...\n")
    result = graph.invoke(initial_state)
    print("\nFINAL REPORT:")
    print(result["report"])