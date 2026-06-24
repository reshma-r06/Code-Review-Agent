"""
ui/app.py
Streamlit frontend for the AI Code Review Agent.
Run with: streamlit run ui/app.py
"""

import streamlit as st
import requests
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_URL = "http://localhost:8000"

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #555;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .decision-approved {
        background: #d4edda; color: #155724;
        padding: 0.8rem 1.5rem; border-radius: 8px;
        font-size: 1.3rem; font-weight: 700;
        border-left: 5px solid #28a745;
    }
    .decision-changes {
        background: #fff3cd; color: #856404;
        padding: 0.8rem 1.5rem; border-radius: 8px;
        font-size: 1.3rem; font-weight: 700;
        border-left: 5px solid #ffc107;
    }
    .decision-reject {
        background: #f8d7da; color: #721c24;
        padding: 0.8rem 1.5rem; border-radius: 8px;
        font-size: 1.3rem; font-weight: 700;
        border-left: 5px solid #dc3545;
    }
    .metric-box {
        background: #f8f9fa; border-radius: 8px;
        padding: 1rem; text-align: center;
        border: 1px solid #dee2e6;
    }
    .issue-critical { border-left: 4px solid #dc3545; padding-left: 12px; margin: 8px 0; }
    .issue-high     { border-left: 4px solid #fd7e14; padding-left: 12px; margin: 8px 0; }
    .issue-medium   { border-left: 4px solid #ffc107; padding-left: 12px; margin: 8px 0; }
    .issue-low      { border-left: 4px solid #28a745; padding-left: 12px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_url = st.text_input("API URL", value=API_URL)
    st.markdown("---")
    st.markdown("### 🏗️ Stack")
    st.markdown("""
    - 🧠 **LLM**: Groq (Llama 3.1 70B)
    - 🔗 **Agents**: LangGraph
    - 📚 **RAG**: ChromaDB + sentence-transformers
    - ⚡ **API**: FastAPI
    """)
    st.markdown("---")
    st.markdown("### 📖 How it works")
    st.markdown("""
    1. **Fetch** — Pull PR diff from GitHub
    2. **Analyze** — Find bugs & security issues  
    3. **Standards** — Check coding standards via RAG
    4. **Tests** — Suggest missing test cases
    5. **Report** — Compile unified review
    """)

# ── Main UI ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🤖 AI Code Review Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-agent PR analysis powered by LangGraph + Groq + ChromaDB RAG</div>', unsafe_allow_html=True)

pr_url = st.text_input(
    "GitHub Pull Request URL",
    placeholder="https://github.com/owner/repo/pull/123",
    help="Paste any public GitHub PR URL",
)

col1, col2 = st.columns([1, 4])
with col1:
    run_btn = st.button("🔍 Review PR", type="primary", use_container_width=True)
with col2:
    if st.button("📥 Ingest Standards", help="Run the vectorstore ingest script first time setup"):
        with st.spinner("Ingesting coding standards into ChromaDB..."):
            try:
                from vectorstore.ingest import ingest_documents
                ingest_documents()
                st.success("✅ Standards ingested successfully!")
            except Exception as e:
                st.error(f"Ingest failed: {e}")

st.markdown("---")

# ── Review Pipeline ────────────────────────────────────────────────────────────
if run_btn and pr_url:
    if "github.com" not in pr_url or "/pull/" not in pr_url:
        st.error("⚠️ Please enter a valid GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    else:
        with st.spinner("🔄 Running multi-agent review pipeline..."):
            progress = st.progress(0, text="Fetching PR from GitHub...")
            try:
                progress.progress(20, text="Fetching PR from GitHub...")
                response = requests.post(
                    f"{api_url}/review",
                    json={"pr_url": pr_url},
                    timeout=120,
                )
                progress.progress(100, text="Done!")

                if response.status_code == 200:
                    data = response.json()
                    progress.empty()

                    # ── Decision Banner ────────────────────────────────────────
                    decision = data.get("merge_decision", "UNKNOWN")
                    if "APPROVED" in decision:
                        css_class = "decision-approved"
                        icon = "✅"
                    elif "MINOR" in decision:
                        css_class = "decision-changes"
                        icon = "⚠️"
                    else:
                        css_class = "decision-reject"
                        icon = "❌"

                    st.markdown(
                        f'<div class="{css_class}">{icon} {decision}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"### {data.get('pr_title', 'PR Review')} — by @{data.get('pr_author', '')}")

                    # ── Metrics Row ────────────────────────────────────────────
                    st.markdown("---")
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Risk Level", data.get("overall_risk", "N/A"))
                    m2.metric("Compliance", f"{data.get('compliance_score', 0)}%")
                    m3.metric("Files Changed", data.get("files_changed", 0))
                    m4.metric("Issues Found", len(data.get("analysis", {}).get("issues", [])))
                    m5.metric("Std Violations", len(data.get("standards", {}).get("violations", [])))

                    st.markdown("---")

                    # ── Tabs ───────────────────────────────────────────────────
                    tab1, tab2, tab3, tab4 = st.tabs(["🐛 Bugs & Security", "📋 Standards", "🧪 Test Coverage", "📄 Raw JSON"])

                    with tab1:
                        analysis = data.get("analysis", {})
                        st.markdown(f"**Summary:** {analysis.get('summary', 'No summary available.')}")
                        issues = analysis.get("issues", [])
                        if issues:
                            for issue in issues:
                                sev = issue.get("severity", "LOW").lower()
                                css = f"issue-{sev}"
                                st.markdown(f"""
<div class="{css}">
<strong>[{issue.get('severity')}] {issue.get('type', '').upper()}</strong> — <code>{issue.get('file', '')}</code><br>
{issue.get('description', '')}<br>
<em>💡 {issue.get('suggestion', '')}</em>
</div>
""", unsafe_allow_html=True)
                        else:
                            st.success("✅ No bugs or security issues detected!")

                    with tab2:
                        standards = data.get("standards", {})
                        compliance = data.get("compliance_score", 100)
                        st.progress(compliance / 100, text=f"Compliance Score: {compliance}%")
                        violations = standards.get("violations", [])
                        if violations:
                            for v in violations:
                                with st.expander(f"⚠️ {v.get('file', 'Unknown file')} — {v.get('standard', '')[:60]}..."):
                                    st.markdown(f"**Standard violated:** {v.get('standard', '')}")
                                    st.markdown(f"**Issue:** {v.get('violation', '')}")
                                    st.markdown(f"**Fix:** {v.get('recommendation', '')}")
                        else:
                            st.success("✅ No standards violations found!")

                    with tab3:
                        tests = data.get("tests", {})
                        st.markdown(f"**Assessment:** {tests.get('coverage_assessment', 'N/A')}")
                        if not tests.get("has_test_files"):
                            st.warning("⚠️ No test files were included in this PR!")
                        missing = tests.get("missing_tests", [])
                        if missing:
                            for item in missing:
                                with st.expander(f"🧪 `{item.get('function_or_class', '')}` in {item.get('file', '')}"):
                                    for tc in item.get("test_cases", []):
                                        st.markdown(f"**{tc.get('test_name', '')}** — {tc.get('scenario', '')}")
                                        st.code(tc.get("test_code", ""), language="python")
                        else:
                            st.success("✅ Test coverage looks good!")

                    with tab4:
                        st.json(data)

                    # Errors
                    if data.get("errors"):
                        st.markdown("---")
                        with st.expander("⚠️ Pipeline warnings"):
                            for err in data["errors"]:
                                st.warning(err)

                else:
                    progress.empty()
                    st.error(f"API Error {response.status_code}: {response.text}")

            except requests.exceptions.ConnectionError:
                progress.empty()
                st.error("❌ Cannot connect to API. Make sure `uvicorn api.main:app --reload` is running.")
            except Exception as e:
                progress.empty()
                st.error(f"Unexpected error: {e}")

elif run_btn and not pr_url:
    st.warning("Please enter a GitHub PR URL first.")
