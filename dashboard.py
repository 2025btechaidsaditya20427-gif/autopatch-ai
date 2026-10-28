import os
import json
import time
import difflib
import subprocess
from datetime import datetime
import streamlit as st
from agent import app

st.set_page_config(page_title="AutoPatchAI Control Center", page_icon="🛡️", layout="wide")

st.title("🛡️ AutoPatchAI — Autonomous Self-Healing CI/CD Agent")
st.caption("LangGraph State Machine • Isolated Sandbox Execution • Multi-Model Gemini Router • Automated GitOps")

# 1. Top Metrics Row
history = []
if os.path.exists("patch_history.json"):
    with open("patch_history.json", "r") as f:
        try:
            history = json.load(f)
        except Exception:
            history = []

col1, col2, col3, col4 = st.columns(4)
total_runs = len(history)
healed_runs = sum(1 for h in history if h.get("status") == "HEALED")
avg_time = round(sum(h.get("time_taken_seconds", 0) for h in history) / total_runs, 2) if total_runs > 0 else 0.0
last_model = history[-1].get("model_used", "gemini-3.6-flash") if history else "gemini-3.6-flash"

col1.metric("Total Healing Runs", total_runs)
col2.metric("Success Rate", f"{int((healed_runs/total_runs)*100)}%" if total_runs else "100%")
col3.metric("Avg Healing Time", f"{avg_time}s")
col4.metric("Active AI Engine", last_model)

st.divider()

# 2. Live Code Editor & Test Suite Viewer
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("🐞 Target Source File (`buggy_app.py`)")
    with open("buggy_app.py", "r") as f:
        current_code = f.read()
    edited_code = st.text_area("Inject a bug here and click Save & Heal:", value=current_code, height=280)

with right_col:
    st.subheader("🧪 Pytest Unit Test Suite (`test_app.py`)")
    with open("test_app.py", "r") as f:
        current_tests = f.read()
    edited_tests = st.text_area("Unit Tests to satisfy:", value=current_tests, height=280)

# 3. Trigger Button
if st.button("🚀 Save Code & Trigger Sandboxed Self-Healing Agent", type="primary", use_container_width=True):
    with open("buggy_app.py", "w") as f:
        f.write(edited_code)
    with open("test_app.py", "w") as f:
        f.write(edited_tests)

    with st.status("🤖 AutoPatchAI Sandboxed Agent is running...", expanded=True) as status:
        st.write("📦 Spinning up Isolated Sandbox & running `pytest`...")
        initial_state = {
            "target_file": "buggy_app.py",
            "test_file": "test_app.py",
            "original_code": edited_code,
            "candidate_code": edited_code,
            "error_logs": "",
            "model_used": "none",
            "iterations": 0,
            "tests_passed": False,
            "start_time": time.time()
        }
        final_state = app.invoke(initial_state)

        if final_state["tests_passed"]:
            status.update(label="✅ Sandbox Tests Passed! Production File Healed!", state="complete", expanded=False)
            st.success(f"Verified in Isolated Sandbox & healed in {final_state['iterations']} iteration(s) using `{final_state['model_used']}`!")
        else:
            status.update(label="❌ Agent reached max retries. Production file kept safe.", state="error")
            st.error("Could not heal all tests within 3 iterations.")

    # Show Unified Diff
    with open("buggy_app.py", "r") as f:
        healed_code = f.read()

    if edited_code != healed_code:
        st.subheader("📊 Verified Sandbox Git Diff Patch")
        diff_lines = list(difflib.unified_diff(
            edited_code.splitlines(),
            healed_code.splitlines(),
            fromfile="a/buggy_app.py (Buggy)",
            tofile="b/buggy_app.py (Healed)",
            lineterm=""
        ))
        st.code("\n".join(diff_lines), language="diff")

st.divider()

# 4. GitOps Automation Section
git_col1, git_col2 = st.columns([2, 1])
with git_col1:
    st.subheader("🌿 GitOps Automated Branch & Commit")
    st.caption("Create an isolated Git branch and commit the AI-verified patch directly from the Control Center.")
with git_col2:
    if st.button("🌿 Create `fix/auto-patch` Branch & Commit", use_container_width=True):
        branch_name = f"fix/autopatch-{datetime.now().strftime('%H%M%S')}"
        subprocess.run(["git", "checkout", "-b", branch_name], capture_output=True)
        subprocess.run(["git", "add", "buggy_app.py"], capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "fix(autopatch): autonomous self-healing patch verified via pytest"],
            capture_output=True, text=True
        )
        st.success(f"✅ Created branch `{branch_name}` & committed verified patch!")

st.divider()
st.subheader("📜 Autonomous Healing Audit Log")
if os.path.exists("patch_history.json"):
    with open("patch_history.json", "r") as f:
        try:
            updated_history = json.load(f)
            if updated_history:
                st.dataframe(updated_history[::-1], use_container_width=True)
        except Exception:
            pass
else:
    st.info("No audit logs yet. Trigger a healing run above to generate logs!")