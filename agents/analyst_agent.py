"""
agents/analyst_agent.py
Analyzes PR diff for bugs, anti-patterns, and security vulnerabilities.
"""

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
import json

load_dotenv()

SYSTEM_PROMPT = """You are a senior software engineer performing a thorough code review.
Your job is to analyze a GitHub Pull Request diff and identify:
1. Bugs: Logic errors, off-by-one errors, null/None handling issues, incorrect conditions
2. Anti-patterns: Code smells, poor design patterns, overly complex code
3. Security vulnerabilities: Injection risks, hardcoded secrets, insecure operations
4. Performance issues: Inefficient algorithms, unnecessary DB calls, memory leaks

Be specific — reference the filename and the problematic code snippet.
Rate each issue as: CRITICAL, HIGH, MEDIUM, or LOW severity.

Respond ONLY with a JSON object in this exact format:
{
  "summary": "Brief 2-sentence overall assessment",
  "issues": [
    {
      "type": "bug|security|anti-pattern|performance",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "file": "filename.py",
      "description": "Clear description of the issue",
      "suggestion": "Concrete fix suggestion"
    }
  ],
  "overall_risk": "HIGH|MEDIUM|LOW"
}

If no issues found, return an empty issues array. Return ONLY valid JSON, no markdown."""


def run_analyst_agent(pr_data: dict, llm: ChatGroq) -> dict:
    """
    Analyze PR diff for bugs and security issues.
    
    Args:
        pr_data: Dict from github_tool.fetch_pr_details()
        llm: Initialized ChatGroq instance
    
    Returns:
        Dict with analysis results
    """
    diff = pr_data.get("diff_summary", "")
    title = pr_data.get("title", "Unknown PR")
    files_changed = [f["filename"] for f in pr_data.get("files", [])]

    user_prompt = f"""Analyze this Pull Request:

**PR Title:** {title}
**Files Changed:** {', '.join(files_changed)}

**Diff:**
```
{diff}
```

Identify all bugs, security issues, anti-patterns, and performance problems."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "summary": "Analysis completed but response parsing failed.",
            "issues": [],
            "overall_risk": "UNKNOWN",
            "raw_response": raw,
        }

    return result
