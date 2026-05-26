"""
Investigation Agent — v0.4

For each exception surfaced by the reconciliation agent:
  1. Embeds the exception description and queries ChromaDB for the 3 most similar
     historical cases from the knowledge base.
  2. Sends the exception + retrieved context to Claude (claude-haiku-4-5) with a
     detailed FinOps domain prompt and structured-output schema.
  3. Collects root_cause, recommended_action, confidence, and exception_category.

Sets state["investigations"] and state["confidence"] (average across all exceptions).
"""

import json
import os
from pathlib import Path

import anthropic
import chromadb

CLAUDE_MODEL = "claude-haiku-4-5"
COLLECTION_NAME = "finops_exceptions"

# System prompt kept verbose so it exceeds Haiku 4.5's 4096-token caching minimum
SYSTEM_PROMPT = """You are a senior FinOps reconciliation analyst with deep expertise in general ledger
accounting, subledger management, financial close processes, and multi-currency operations across
global enterprises. You specialise in diagnosing financial exceptions: mismatches between the general
ledger (GL) and subledger, FX conversion discrepancies, period-cut-off errors, intercompany
settlement failures, manual journal issues, and GL chart-of-account coding errors.

Your responsibilities in this pipeline:
- Receive a structured description of the current financial exception (account code, variance amount
  in USD, currency, entity, and exception type).
- Review up to three historically similar exceptions retrieved from the team's knowledge base,
  including how those past cases were resolved and in how many days.
- Apply your domain expertise to determine the most likely root cause of the current exception,
  drawing on the patterns in the historical cases but also considering the specifics of the current
  exception.
- Recommend a concrete, actionable remediation step that the finance team can execute today.
- Assign a confidence score between 0.0 and 1.0 reflecting how certain you are of your root-cause
  diagnosis. A high score (>=0.8) means the historical cases are closely analogous and the diagnosis
  is clear. A lower score (<0.8) means the current exception has unusual characteristics that do not
  map neatly to the retrieved cases and warrants human review.
- Categorise the exception into exactly one of the following categories:
    FX_TIMING         — rate-date mismatch between GL and subledger (trade vs settlement date, etc.)
    GL_CODING_ERROR   — transaction posted to wrong account code or cost centre
    INTERCOMPANY      — intercompany elimination / settlement timing mismatch
    PERIOD_CUTOFF     — transaction recorded in wrong accounting period
    SYSTEM_ERROR      — batch job failure, interface outage, scheduler issue
    MANUAL_JOURNAL    — manual journal entry applied to one side only (GL or subledger, not both)
    OTHER             — root cause does not fit any of the above categories

Tone and output format:
- root_cause: one or two plain-English sentences explaining what caused the discrepancy.
  Be specific — reference account series, currencies, and likely system or process failure points.
- recommended_action: one or two actionable sentences. Begin with a verb (e.g., "Re-run ...",
  "Post a correcting ...", "Escalate to ...", "Review and align ...").
- confidence: a float between 0.0 and 1.0, rounded to two decimal places.
- exception_category: one of the seven category strings listed above.

Do not add commentary or explanation outside the JSON structure. Do not invent account balances,
reference numbers, or names. Work only from the data provided.

Domain context you should keep in mind:
- FX_DISCREPANCY exceptions on GBP or EUR accounts almost always stem from rate-date mismatches,
  revaluation job failures, or hedge accounting rate differences. The variance magnitude divided by
  the FX rate gives you the approximate local-currency amount affected, which can help you reason
  about whether the size of the exception is plausible for the account type.
- GL_MISMATCH exceptions on USD accounts suggest a direct balance difference: either a coding error,
  a manual journal applied to one source only, or a timing difference in transaction posting.
- GL_ONLY means a record exists in the GL but not in the subledger — likely a manual GL entry, a
  direct posting, or a subledger feed failure.
- SUBLEDGER_ONLY means a record exists in the subledger but not in the GL — likely a subledger
  transaction that was not fed through to the GL, or a GL reversal that was not mirrored.
- Variance amounts in this system are expressed in USD after FX conversion. Amounts above $50,000
  should be treated as high-severity and may warrant same-day escalation.
- The period field (e.g., "2024-09") represents the accounting month. Exceptions with the current
  period are more urgent than prior-period exceptions which may already be under investigation.
- Resolution days from the knowledge base give you a sense of urgency: if similar historical cases
  were resolved in 1-2 days, recommend a quick fix; if they averaged 5-10 days, the fix likely
  requires multiple stakeholders or system access.

Think step by step, but output only the JSON. Your output must conform exactly to the schema
provided by the caller."""


def _get_collection(vector_store_path: str) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=vector_store_path)
    return client.get_collection(name=COLLECTION_NAME)


def _retrieve_similar(collection: chromadb.Collection, exception: dict, n: int = 3) -> list[dict]:
    """Query ChromaDB for the n most similar historical exceptions."""
    query_text = (
        f"{exception['type']} on account {exception['account']} "
        f"currency {exception['currency']} entity {exception.get('entity', 'unknown')} "
        f"variance ${exception['variance']:,.0f} USD"
    )
    results = collection.query(query_texts=[query_text], n_results=n)

    similar = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        # Cosine distance in ChromaDB = 1 - cosine_similarity
        similarity = round(1.0 - distance, 4)
        similar.append({
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "similarity": similarity,
        })
    return similar


def _build_user_message(exception: dict, similar: list[dict]) -> str:
    lines = [
        "## Current Exception",
        f"- Account code  : {exception['account']}",
        f"- Exception type: {exception['type']}",
        f"- Currency      : {exception['currency']}",
        f"- Entity        : {exception.get('entity', 'unknown')}",
        f"- GL balance    : ${exception['source_a']:,.2f} USD",
        f"- SL balance    : ${exception['source_b']:,.2f} USD",
        f"- Variance      : ${exception['variance']:,.2f} USD",
        "",
        "## Similar Historical Cases",
    ]
    for i, case in enumerate(similar, start=1):
        m = case["metadata"]
        lines += [
            f"### Case {i} (similarity {case['similarity']:.2%})",
            case["document"],
            f"- Root cause     : {m.get('root_cause', 'n/a')}",
            f"- Resolution     : {m.get('resolution', 'n/a')}",
            f"- Resolution days: {m.get('resolution_days', 'n/a')}",
            "",
        ]
    lines.append("Diagnose the current exception and respond with the JSON schema.")
    return "\n".join(lines)


def _call_claude(anthropic_client: anthropic.Anthropic, user_message: str) -> dict:
    response = anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "root_cause": {"type": "string"},
                        "recommended_action": {"type": "string"},
                        "confidence": {"type": "number"},
                        "exception_category": {
                            "type": "string",
                            "enum": [
                                "FX_TIMING",
                                "GL_CODING_ERROR",
                                "INTERCOMPANY",
                                "PERIOD_CUTOFF",
                                "SYSTEM_ERROR",
                                "MANUAL_JOURNAL",
                                "OTHER",
                            ],
                        },
                    },
                    "required": [
                        "root_cause",
                        "recommended_action",
                        "confidence",
                        "exception_category",
                    ],
                    "additionalProperties": False,
                },
            }
        },
    )
    return json.loads(response.content[0].text)


def investigation_agent(state: dict) -> dict:
    """LangGraph node: RAG + Claude root-cause analysis for each exception."""
    print("Agent 2: Investigation Agent running...")

    base = Path(__file__).parent.parent
    vector_store_path = str(base / "data" / "vector_store")

    anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    collection = _get_collection(vector_store_path)

    investigations = []
    confidence_scores = []

    for exception in state["exceptions"]:
        similar = _retrieve_similar(collection, exception)
        user_message = _build_user_message(exception, similar)
        try:
            result = _call_claude(anthropic_client, user_message)
        except Exception as exc:
            print(
                f"  ERROR — Claude API call failed for {exception['account']} "
                f"({exception['type']}): {type(exc).__name__}: {exc}"
            )
            raise

        investigations.append({
            "account": exception["account"],
            "exception_type": exception["type"],
            "variance": exception["variance"],
            "currency": exception["currency"],
            "root_cause": result["root_cause"],
            "recommended_action": result["recommended_action"],
            "confidence": result["confidence"],
            "exception_category": result["exception_category"],
            "similar_cases": [c["id"] for c in similar],
        })
        confidence_scores.append(result["confidence"])
        print(
            f"  {exception['account']} ({exception['type']}) — "
            f"category={result['exception_category']} confidence={result['confidence']:.2f}"
        )

    state["investigations"] = investigations
    state["confidence"] = (
        round(sum(confidence_scores) / len(confidence_scores), 4)
        if confidence_scores
        else 0.0
    )
    print(f"  Average confidence: {state['confidence']:.2f}")
    return state
