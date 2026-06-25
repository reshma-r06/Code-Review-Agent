# AI Code Review Agent

### A multiagent system that autonomously reviews GitHub Pull Requests
-  Detects bugs
-  Checks coding standards via RAG
-  Suggests missing tests 
-  Delivers merge decisions

Paste any GitHub PR URL → get a complete automated review in ~15 seconds:
-  Bug & Security Analysis — Detects logic errors, security vulnerabilities, anti-patterns
-  Standards Compliance — RAG-powered check against your team's coding standards
-  Test Coverage Review — Identifies missing test cases with runnable pytest stubs
-  Merge Decision — APPROVED / NEEDS MINOR CHANGES / CHANGES REQUESTED
Built entirely on free, open-source tools — no OpenAI, no paid APIs, runs on CPU only.

#### Agent Design
-  Analyst Agent -> Llama 3.1 70B (Groq) -> Input: PR diff -> Output: JSON: bugs, severity, suggestions
  
-  RAG Agent -> Llama 3.1 70B + ChromaDB -> Input: PR diff + retrieved standards -> Output: JSON: violations, compliance score

-  Test Agent -> Llama 3.1 70B (Groq) -> Input: PR diff -> Output: JSON: missing tests, pytest stubs

-  Orchestrator -> LangGraph StateGraph -> Input: Full ReviewState -> Output: Compiled final report

All agents use structured JSON output with explicit prompting — no regex parsing of free-form text.

-  Python 3.11+
-  Groq API key (free)
-  GitHub Personal Access Token
-  Agent Orchestration -> LangGraph 0.4+ (Stateful multi-agent graph with conditional routing)
-  LLMGroq API -> Llama 3.1 70B(Free tier, 500+ tokens/sec, no GPU needed)
-  Embeddings -> sentence-transformers all-MiniLM-L6-v2(Local CPU embeddings, zero cost)
-  Vector Store -> ChromaDB(Persistent local vector store for coding standards)
-  GitHub Integration -> PyGithub(PR diff and metadata fetching)
-  API Layer -> FastAPI(REST endpoint with Pydantic validation)
-  Frontend -> Streamlit(Interactive review dashboard)
-  LLM Framework -> LangChain Core(Message formatting, prompt management)

  
  <img width="1376" height="868" alt="image" src="https://github.com/user-attachments/assets/64b86f25-b9e1-4ac3-9960-cafe1ba83257" />

  <img width="1372" height="870" alt="image" src="https://github.com/user-attachments/assets/adc18dc8-13c8-4010-933a-334363cef9c6" />

  <img width="1372" height="869" alt="image" src="https://github.com/user-attachments/assets/52538042-82e2-489f-aacb-2f46dafd6702" />

  <img width="1372" height="872" alt="image" src="https://github.com/user-attachments/assets/030bfe6e-0023-4fc3-b9f5-65f0d79fbb6b" />

  




