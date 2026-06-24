"""
api/main.py
FastAPI backend exposing the code review agent pipeline.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv

from graph.workflow import run_review

load_dotenv()

app = FastAPI(
    title="AI Code Review Agent",
    description="Multi-agent PR review powered by LangGraph + Groq + ChromaDB",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    pr_url: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "pr_url": "https://github.com/owner/repo/pull/123"
            }
        }
    }


class ReviewResponse(BaseModel):
    pr_title: str
    pr_author: str
    merge_decision: str
    overall_risk: str
    compliance_score: int
    files_changed: int
    analysis: dict
    standards: dict
    tests: dict
    errors: list


@app.get("/")
def health_check():
    return {"status": "running", "service": "AI Code Review Agent"}


@app.post("/review", response_model=ReviewResponse)
def review_pr(request: ReviewRequest):
    """
    Run the full multi-agent code review pipeline on a GitHub PR.
    
    - Fetches PR diff from GitHub
    - Runs bug/security analysis agent
    - Checks coding standards via RAG agent  
    - Suggests missing tests via test agent
    - Compiles unified report with merge decision
    """
    if "github.com" not in request.pr_url or "/pull/" not in request.pr_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid PR URL. Must be a full GitHub PR URL like https://github.com/owner/repo/pull/123",
        )

    report = run_review(request.pr_url)

    if not report:
        raise HTTPException(status_code=500, detail="Review pipeline returned empty report.")

    return ReviewResponse(**{
        "pr_title": report.get("pr_title", ""),
        "pr_author": report.get("pr_author", ""),
        "merge_decision": report.get("merge_decision", "UNKNOWN"),
        "overall_risk": report.get("overall_risk", "UNKNOWN"),
        "compliance_score": report.get("compliance_score", 0),
        "files_changed": report.get("files_changed", 0),
        "analysis": report.get("analysis", {}),
        "standards": report.get("standards", {}),
        "tests": report.get("tests", {}),
        "errors": report.get("errors", []),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
