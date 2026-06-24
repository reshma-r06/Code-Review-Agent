"""
agents/test_agent.py
Suggests missing test cases based on the PR diff.
"""

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import json

load_dotenv()

SYSTEM_PROMPT = """You are a senior QA engineer and test architect.
Analyze a GitHub PR diff and identify missing or insufficient test coverage.

For each changed function or class, suggest specific test cases covering:
- Happy path (expected inputs and outputs)
- Edge cases (empty inputs, boundary values, None/null)
- Error/exception paths
- Any security-sensitive inputs that need validation testing

Respond ONLY with a JSON object in this exact format:
{
  "coverage_assessment": "Brief assessment of existing test coverage in the PR",
  "missing_tests": [
    {
      "function_or_class": "name of the function/class to test",
      "file": "filename.py",
      "test_cases": [
        {
          "test_name": "test_descriptive_name",
          "scenario": "What this test covers",
          "test_code": "def test_descriptive_name():\\n    # pytest-style test code here\\n    pass"
        }
      ]
    }
  ],
  "has_test_files": true,
  "recommended_framework": "pytest"
}

Keep test_code concise but runnable. Return ONLY valid JSON, no markdown."""


def run_test_agent(pr_data: dict, llm: ChatGroq) -> dict:
    """
    Suggest missing test cases for the PR.
    
    Args:
        pr_data: Dict from github_tool.fetch_pr_details()
        llm: Initialized ChatGroq instance
    
    Returns:
        Dict with test suggestions
    """
    diff = pr_data.get("diff_summary", "")
    files = pr_data.get("files", [])
    file_names = [f["filename"] for f in files]

    # Check if any test files are in the PR
    test_files = [f for f in file_names if "test" in f.lower() or "spec" in f.lower()]
    source_files = [f for f in file_names if "test" not in f.lower()]

    user_prompt = f"""Analyze this PR and suggest missing tests:

**Source files changed:** {', '.join(source_files) if source_files else 'None'}
**Test files included:** {', '.join(test_files) if test_files else 'None — no test files in this PR!'}

**PR Diff:**
```
{diff}
```

Suggest specific, runnable pytest test cases for all changed functions and edge cases."""

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
            "coverage_assessment": "Could not parse test suggestions.",
            "missing_tests": [],
            "has_test_files": len(test_files) > 0,
            "recommended_framework": "pytest",
            "raw_response": raw,
        }

    return result