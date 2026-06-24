"""
tools/github_tool.py
Fetches PR metadata and diff from GitHub using PyGithub.
"""

import os
import re
from github import Github
from dotenv import load_dotenv

load_dotenv()


def parse_pr_url(pr_url: str) -> tuple[str, int]:
    """Extract owner/repo and PR number from a GitHub PR URL."""
    pattern = r"github\.com/([^/]+/[^/]+)/pull/(\d+)"
    match = re.search(pattern, pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
    repo_full_name = match.group(1)
    pr_number = int(match.group(2))
    return repo_full_name, pr_number


def fetch_pr_details(pr_url: str) -> dict:
    """
    Fetch PR title, description, and file diffs from GitHub.

    Returns a dict with:
        - title: PR title
        - description: PR body
        - author: PR author login
        - files: list of {filename, status, additions, deletions, patch}
        - diff_summary: combined diff text (truncated for LLM context)
    """
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token) if token else Github()

    repo_name, pr_number = parse_pr_url(pr_url)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    files = []
    diff_chunks = []

    for f in pr.get_files():
        file_info = {
            "filename": f.filename,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
            "patch": f.patch or "(binary or no patch available)",
        }
        files.append(file_info)
        if f.patch:
            diff_chunks.append(f"### {f.filename} ({f.status})\n{f.patch}")

    # Keep diff under ~6000 chars to stay within context limits
    full_diff = "\n\n".join(diff_chunks)
    if len(full_diff) > 6000:
        full_diff = full_diff[:6000] + "\n\n... [diff truncated for context window]"

    return {
        "title": pr.title,
        "description": pr.body or "No description provided.",
        "author": pr.user.login,
        "base_branch": pr.base.ref,
        "head_branch": pr.head.ref,
        "files": files,
        "diff_summary": full_diff,
        "changed_files_count": len(files),
        "total_additions": sum(f["additions"] for f in files),
        "total_deletions": sum(f["deletions"] for f in files),
    }


if __name__ == "__main__":
    # Quick test
    url = input("Enter a public GitHub PR URL: ")
    details = fetch_pr_details(url)
    print(f"\nPR: {details['title']}")
    print(f"Files changed: {details['changed_files_count']}")
    print(f"Diff preview:\n{details['diff_summary'][:500]}")
