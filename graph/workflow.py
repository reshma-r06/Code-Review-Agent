"""
graph/workflow.py
LangGraph multi-agent orchestration for the code review pipeline.
"""

import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
import operator

load_dotenv()

# ── Imports from sibling packages ──────────────────────────────────────────────
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.github_tool import fetch_pr_details
from agents.analyst_agent import run_analyst_agent
from agents.rag_agent import run_rag_agent
from agents.test_agent import run_test_agent


# ── State Definition ───────────────────────────────────────────────────────────

class ReviewState(TypedDict):
    """Shared state passed between all graph nodes."""
    pr_url: str
    pr_data: dict           # raw PR metadata + diff from GitHub
    analysis: dict          # output from analyst_agent
    standards: dict         # output from rag_agent
    test_suggestions: dict  # output from test_agent
    final_report: dict      # compiled final report
    errors: Annotated[list[str], operator.add]  # accumulate errors from any node


# ── LLM Initialization ────────────────────────────────────────────────────────

def get_llm() -> ChatGroq:
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY"),
    )


# ── Node Functions ─────────────────────────────────────────────────────────────

def fetch_pr_node(state: ReviewState) -> dict:
    """Node 1: Fetch PR details from GitHub."""
    print(f"[Node] fetch_pr → {state['pr_url']}")
    try:
        pr_data = fetch_pr_details(state["pr_url"])
        # ONLY return the field this node updates
        return {"pr_data": pr_data}
    except Exception as e:
        return {"pr_data": {}, "errors": [f"fetch_pr failed: {str(e)}"]}


def analyst_node(state: ReviewState) -> dict:
    """Node 2a: Run bug and security analysis."""
    print("[Node] analyst_agent → analyzing diff...")
    if not state.get("pr_data"):
        return {"analysis": {}, "errors": ["analyst_node: no pr_data available"]}
    try:
        llm = get_llm()
        result = run_analyst_agent(state["pr_data"], llm)
        # ONLY return your update
        return {"analysis": result}
    except Exception as e:
        return {"analysis": {}, "errors": [f"analyst_node failed: {str(e)}"]}


def rag_node(state: ReviewState) -> dict:
    """Node 2b: Check against coding standards via RAG."""
    print("[Node] rag_agent → checking coding standards...")
    if not state.get("pr_data"):
        return {"standards": {}, "errors": ["rag_node: no pr_data available"]}
    try:
        llm = get_llm()
        result = run_rag_agent(state["pr_data"], llm)
        # ONLY return your update
        return {"standards": result}
    except Exception as e:
        return {"standards": {}, "errors": [f"rag_node failed: {str(e)}"]}


def test_node(state: ReviewState) -> dict:
    """Node 2c: Suggest missing test cases."""
    print("[Node] test_agent → generating test suggestions...")
    if not state.get("pr_data"):
        return {"test_suggestions": {}, "errors": ["test_node: no pr_data available"]}
    try:
        llm = get_llm()
        result = run_test_agent(state["pr_data"], llm)
        # ONLY return your update
        return {"test_suggestions": result}
    except Exception as e:
        return {"test_suggestions": {}, "errors": [f"test_node failed: {str(e)}"]}


def compile_report_node(state: ReviewState) -> dict:
    """Node 3: Compile all agent outputs into a unified report."""
    print("[Node] compile_report → building final report...")

    pr = state.get("pr_data", {})
    analysis = state.get("analysis", {})
    standards = state.get("standards", {})
    tests = state.get("test_suggestions", {})

    # Compute a merged risk score
    risk_map = {"HIGH": 3, "CRITICAL": 4, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 1}
    analysis_risk = risk_map.get(analysis.get("overall_risk", "LOW"), 1)
    compliance_score = standards.get("compliance_score", 100)
    has_tests = tests.get("has_test_files", True)

    if analysis_risk >= 3 or compliance_score < 50:
        merge_decision = "CHANGES REQUESTED"
    elif analysis_risk == 2 or compliance_score < 75 or not has_tests:
        merge_decision = "NEEDS MINOR CHANGES"
    else:
        merge_decision = "APPROVED"

    final_report = {
        "pr_url": state["pr_url"],
        "pr_title": pr.get("title", "N/A"),
        "pr_author": pr.get("author", "N/A"),
        "files_changed": pr.get("changed_files_count", 0),
        "additions": pr.get("total_additions", 0),
        "deletions": pr.get("total_deletions", 0),
        "merge_decision": merge_decision,
        "overall_risk": analysis.get("overall_risk", "UNKNOWN"),
        "compliance_score": compliance_score,
        "analysis": {
            "summary": analysis.get("summary", ""),
            "issues": analysis.get("issues", []),
        },
        "standards": {
            "violations": standards.get("violations", []),
            "standards_checked": standards.get("standards_checked", []),
        },
        "tests": {
            "coverage_assessment": tests.get("coverage_assessment", ""),
            "missing_tests": tests.get("missing_tests", []),
            "has_test_files": tests.get("has_test_files", False),
        },
        "errors": state.get("errors", []),
    }

    print(f"[Node] compile_report → decision: {merge_decision}")
    # ONLY return your update
    return {"final_report": final_report}


# ── Conditional Edge: skip agents if PR fetch failed ──────────────────────────

def should_continue(state: ReviewState) -> str:
    """Route to agents only if PR data was successfully fetched."""
    if not state.get("pr_data"):
        return "compile_report"
    return "run_agents"


# ── Graph Assembly ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(ReviewState)

    # Add nodes
    graph.add_node("fetch_pr", fetch_pr_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("rag", rag_node)
    graph.add_node("test", test_node)
    graph.add_node("compile_report", compile_report_node)

    # Edges
    graph.add_edge(START, "fetch_pr")

    # Conditional: if fetch failed, skip to compile
    graph.add_conditional_edges(
        "fetch_pr",
        should_continue,
        {
            "run_agents": "analyst",   # normal path: route to the start of parallel block
            "compile_report": "compile_report",  # error path
        },
    )

    # Fan-out layout from the conditional entry point
    # Since 'fetch_pr' unconditionally forks to 'rag' and 'test', we define the fan-out structure clearly:
    graph.add_edge("fetch_pr", "rag")
    graph.add_edge("fetch_pr", "test")
    
    # Fan-in (Sync back up at compilation)
    graph.add_edge("analyst", "compile_report")
    graph.add_edge("rag", "compile_report")
    graph.add_edge("test", "compile_report")
    graph.add_edge("compile_report", END)

    return graph.compile()


def run_review(pr_url: str) -> dict:
    """Main entry point: run the full code review pipeline."""
    app = build_graph()
    initial_state = ReviewState(
        pr_url=pr_url,
        pr_data={},
        analysis={},
        standards={},
        test_suggestions={},
        final_report={},
        errors=[],
    )
    final_state = app.invoke(initial_state)
    return final_state["final_report"]


if __name__ == "__main__":
    url = input("Enter GitHub PR URL: ")
    report = run_review(url)
    import json
    print(json.dumps(report, indent=2))