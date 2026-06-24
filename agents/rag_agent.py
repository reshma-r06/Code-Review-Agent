"""
agents/rag_agent.py
Retrieves relevant coding standards from ChromaDB and checks PR against them.
"""

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vectorstore.ingest import query_standards

load_dotenv()

SYSTEM_PROMPT = """You are a code standards compliance reviewer.
You will be given:
1. A GitHub PR diff
2. Relevant sections from the team's coding standards

Your job is to check if the PR code violates any of the provided standards.
Be specific — quote the exact standard being violated and the code that violates it.

Respond ONLY with a JSON object in this exact format:
{
  "standards_checked": ["list of standard names/sections you checked against"],
  "violations": [
    {
      "standard": "The exact standard rule being violated",
      "file": "filename where violation occurs",
      "violation": "What the code does wrong",
      "recommendation": "How to fix it to comply with the standard"
    }
  ],
  "compliance_score": 85
}

compliance_score is 0-100 where 100 = fully compliant.
Return ONLY valid JSON, no markdown."""


def run_rag_agent(pr_data: dict, llm: ChatGroq) -> dict:
    """
    Check PR against coding standards retrieved from vector store.
    
    Args:
        pr_data: Dict from github_tool.fetch_pr_details()
        llm: Initialized ChatGroq instance
    
    Returns:
        Dict with standards compliance results
    """
    diff = pr_data.get("diff_summary", "")
    files = [f["filename"] for f in pr_data.get("files", [])]

    # Build queries from file types and diff content
    queries = [
        "naming conventions and code style",
        "error handling best practices",
        "security input validation secrets",
        "testing requirements coverage",
    ]

    # Retrieve relevant standards chunks
    retrieved_chunks = []
    seen_content = set()
    for query in queries:
        try:
            results = query_standards(query, n_results=2)
            for r in results:
                if r["content"] not in seen_content:
                    retrieved_chunks.append(r)
                    seen_content.add(r["content"])
        except Exception:
            # Vector store may not be initialized yet
            pass

    if not retrieved_chunks:
        return {
            "standards_checked": [],
            "violations": [],
            "compliance_score": 100,
            "note": "No standards documents found in vector store. Run vectorstore/ingest.py first.",
        }

    standards_text = "\n\n---\n\n".join(
        [f"[From: {c['source']}]\n{c['content']}" for c in retrieved_chunks]
    )

    user_prompt = f"""Check this PR against our coding standards:

**Files Changed:** {', '.join(files)}

**PR Diff:**
```
{diff}
```

**Relevant Coding Standards:**
{standards_text}

Identify any standards violations."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "standards_checked": [],
            "violations": [],
            "compliance_score": 0,
            "raw_response": raw,
        }

    return result
