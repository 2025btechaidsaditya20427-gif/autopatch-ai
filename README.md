# 🛡️ AutoPatchAI — Autonomous Self-Healing CI/CD Code Agent

An autonomous software engineering agent powered by **LangGraph** and **Gemini Flash Multi-Model Routing** that detects failing unit tests, synthesizes code patches, verifies fixes inside an **Isolated Sandbox**, and automates **GitOps branch/commit workflows**.

## ✨ Key Engineering Highlights
- **Stateful Agentic Loop (LangGraph):** Cyclic state machine (`run_tests` ➔ `fix_code` ➔ `verify`) with deterministic termination.
- **Zero-Risk Isolated Sandboxing:** Candidate AI patches are tested in ephemeral `tempfile` environments before touching production files.
- **Fault-Tolerant Multi-Model Router:** Automatic fallback across `gemini-3.6-flash`, `gemini-3.7-flash`, and `gemini-3.8-flash` with exponential backoff to handle 503/429 rate limits.
- **Live Streamlit Control Center:** Real-time code injection, Unified Git Diff visualization, JSON audit logging, and one-click GitOps branch commits.

## 🚀 Quick Start
```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key"
python3 -m streamlit run dashboard.py