import os
import json
import time
import difflib
import subprocess
from datetime import datetime
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY nahi mili! .env file check karo.")

class AgentState(TypedDict):
    target_file: str
    test_file: str
    original_code: str
    fixed_code: str
    error_logs: str
    model_used: str
    iterations: int
    tests_passed: bool
    start_time: float

def call_gemini(prompt: str) -> tuple[str, str]:
    """Smart Retry + Exponential Backoff across active Flash models"""
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.8-flash"
    ]
    
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    })

    for attempt in range(1, 6):
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
            result = subprocess.run(
                [
                    "curl", "-s", "-X", "POST", url,
                    "-H", "Content-Type: application/json",
                    "--max-time", "60",
                    "-d", payload
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                continue
                
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                continue

            if "error" in data:
                msg = data["error"].get("message", "")
                print(f"⏳ {model} busy ({msg[:40]}...). Switching...", flush=True)
                time.sleep(2)
                continue
            
            parts = data["candidates"][0]["content"]["parts"]
            for part in reversed(parts):
                if "text" in part and not part.get("thought", False):
                    print(f"✨ Fixed using model: {model}", flush=True)
                    return part["text"], model
            return parts[-1]["text"], model
            
        wait_sec = attempt * 4
        print(f"🔄 Attempt {attempt}/5 complete. Waiting {wait_sec}s for server load to clear...", flush=True)
        time.sleep(wait_sec)
        
    raise RuntimeError("❌ Google servers abhi bohot busy hain. Thodi der baad try karein.")

def print_colored_diff(old_code: str, new_code: str, filename: str):
    """Terminal par GitHub style Green/Red Git Diff print karta hai"""
    print("\n" + "="*60)
    print(f"📊 GIT DIFF PATCH REPORT FOR: {filename}")
    print("="*60)
    diff = difflib.unified_diff(
        old_code.splitlines(),
        new_code.splitlines(),
        fromfile=f"a/{filename} (Buggy)",
        tofile=f"b/{filename} (Healed)",
        lineterm=""
    )
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print(f"\033[92m{line}\033[0m")  # Green for added lines
        elif line.startswith("-") and not line.startswith("---"):
            print(f"\033[91m{line}\033[0m")  # Red for removed lines
        elif line.startswith("@@"):
            print(f"\033[96m{line}\033[0m")  # Cyan for line numbers
        else:
            print(line)
    print("="*60 + "\n")

def save_audit_log(state: AgentState):
    """Dashboard ke liye patch_history.json mein record save karta hai"""
    log_file = "patch_history.json"
    history = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                history = json.load(f)
            except Exception:
                history = []
                
    duration = round(time.time() - state["start_time"], 2)
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_file": state["target_file"],
        "model_used": state["model_used"],
        "iterations_taken": state["iterations"],
        "time_taken_seconds": duration,
        "status": "HEALED" if state["tests_passed"] else "FAILED"
    }
    history.append(entry)
    with open(log_file, "w") as f:
        json.dump(history, f, indent=2)
    print(f"📁 Audit log saved to {log_file} (Time taken: {duration}s)", flush=True)

def run_tests(state: AgentState):
    print(f"\n🔍 [Step {state['iterations'] + 1}] Running pytest on {state['test_file']}...", flush=True)
    result = subprocess.run(
        ["pytest", state["test_file"], "--tb=short"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ All tests PASSED! Code is completely healed.", flush=True)
        state["tests_passed"] = True   # <--- BAS YAHAN PAR YEH LINE JODNI HAI!
        if state["iterations"] > 0:
            print_colored_diff(state["original_code"], state["fixed_code"], state["target_file"])
            save_audit_log(state)
        return {"tests_passed": True, "error_logs": ""}
    else:
        print("❌ Tests FAILED! Sending error logs to AI Surgeon...", flush=True)
        return {"tests_passed": False, "error_logs": result.stdout}
def fix_code(state: AgentState):
    print("🛠️ AI Surgeon is analyzing the bug and writing a patch...", flush=True)
    
    with open(state["target_file"], "r") as f:
        buggy_code = f.read()
    with open(state["test_file"], "r") as f:
        test_code = f.read()

    prompt = f"""You are an Autonomous Bug-Fixing AI Agent.
Fix the bugs in the target Python file so that all pytest unit tests pass.

--- TARGET FILE ({state['target_file']}) ---
{buggy_code}

--- TEST FILE ({state['test_file']}) ---
{test_code}

--- PYTEST ERROR LOGS ---
{state['error_logs']}

Return ONLY the complete, fixed Python code for {state['target_file']}. 
Do NOT include markdown formatting like ```python or any explanations."""

    print("📡 Calling Gemini API...", flush=True)
    raw_response, model_used = call_gemini(prompt)
    fixed_code = raw_response.strip()
    print("⚡ Response received from Gemini!", flush=True)
    
    if fixed_code.startswith("```"):
        lines = fixed_code.split("\n")
        fixed_code = "\n".join(lines[1:-1])

    with open(state["target_file"], "w") as f:
        f.write(fixed_code)
        
    print("📝 Patch applied to file!", flush=True)
    return {
        "iterations": state["iterations"] + 1,
        "fixed_code": fixed_code,
        "model_used": model_used
    }

def should_continue(state: AgentState):
    if state["tests_passed"]:
        return END
    if state["iterations"] >= 3:
        print("⚠️ Max retries (3) reached. Stopping agent.", flush=True)
        save_audit_log(state)
        return END
    return "fix_code"

workflow = StateGraph(AgentState)
workflow.add_node("run_tests", run_tests)
workflow.add_node("fix_code", fix_code)

workflow.set_entry_point("run_tests")
workflow.add_conditional_edges("run_tests", should_continue)
workflow.add_edge("fix_code", "run_tests")

app = workflow.compile()

if __name__ == "__main__":
    print("🚀 Starting AutoPatchAI Self-Healing Loop (v2.0 with Git Diff)...", flush=True)
    with open("buggy_app.py", "r") as f:
        initial_code = f.read()
        
    initial_state = {
        "target_file": "buggy_app.py",
        "test_file": "test_app.py",
        "original_code": initial_code,
        "fixed_code": initial_code,
        "error_logs": "",
        "model_used": "none",
        "iterations": 0,
        "tests_passed": False,
        "start_time": time.time()
    }
    app.invoke(initial_state)