
# agent.py
# Browser automation agent using Playwright MCP over HTTP/SSE.
# Executes natural-language testcases and writes a PASS/FAIL summary to test_reports/results.md
#
# Usage:
#   1) Start the Playwright MCP server (HTTP/SSE):
#      npx @playwright/mcp@latest --port 8931 --executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
#   2) Run:
#      adk run root_agent
#
# Then prompt, for example:
#   goto flipkart site, close the login pop-up, search for t-shirt, select first one, add to cart.
#   after completion collect the summary of the testcase




# for making A2A speaking agent and run server add some line bellow it:
# Convert the ADK agent to an A2A-ready FastAPI app (auto-generates Agent Card)

#import uvicorn
# from google.adk.a2a.utils.agent_to_a2a import to_a2a 
# A2A_PORT = int(os.getenv("A2A_PORT", "8001"))# Port appears in the Agent Card URL; uvicorn must match it.
# A2A_HOST = os.getenv("A2A_HOST", "0.0.0.0")
# a2a_app = to_a2a(root_agent, port=A2A_PORT)# Wrap your ADK agent for A2A

# run command:
#    cd my_agent
#    uvicorn agent:a2a_app --host localhost --port 8001
# card generated here: http://127.0.0.1:8001/.well-known/agent-card.json

import os
import json
from datetime import datetime

from dotenv import load_dotenv
import litellm

# --- ADK imports ---
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.agents import LlmAgent

# =========================
# Environment & Model Setup
# =========================
load_dotenv()
litellm.ssl_verify = False  # as you had in your snippet

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

# Build the LiteLLM-backed model object (OpenAI via LiteLLM)
openai_llm = LiteLlm(
    model="openai/gpt-5",
    api_key=OPENAI_API_KEY, 
)

# =========================
# MCP (Playwright) Toolset
# =========================
# Use HTTP/SSE mode. The SSE endpoint is /sse; unified MCP endpoint is /mcp.
# We connect to SSE as recommended by ADK for external MCP servers.
# Refs:
#  - Playwright MCP (HTTP/SSE quick start & endpoints) — microsoft/playwright-mcp README & docs
#  - ADK MCPToolset with SSE connection parameters
MCP_SSE_URL = os.getenv("PLAYWRIGHT_MCP_SSE_URL", "http://localhost:8931/sse")
playwright_mcp = MCPToolset(
    connection_params=SseConnectionParams(
        url=MCP_SSE_URL
    )
)

# =========================
# Test/Report Utilities
# =========================
def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def generate_test_suites_file() -> str | None:
    """
    Ensure test_suites.md exists. If present, touch to update mtime; otherwise create stub.
    """
    target = os.path.join(repo_root(), "test_suites.md")
    try:
        if os.path.exists(target):
            os.utime(target, times=None)  # touch
            return target
        with open(target, "w", encoding="utf-8") as f:
            f.write("# Generated Test Suites\n\nPlease fill with test cases.\n")
        return target
    except Exception as e:
        print(f"[agent] Failed to write test_suites.md: {e}")
        return None

def read_latest_report_summary(max_chars: int = 2000) -> str | None:
    """
    Read markdown report at test_reports/results.md and return truncated content.
    """
    rpt = os.path.join(repo_root(), "test_reports", "results.md")
    if not os.path.exists(rpt):
        return None
    try:
        with open(rpt, "r", encoding="utf-8") as f:
            return f.read()[:max_chars]
    except Exception as e:
        return f"Failed to read report: {e}"

def ensure_reports_dir() -> str:
    path = os.path.join(repo_root(), "test_reports")
    os.makedirs(path, exist_ok=True)
    return path

# =========================
# Local Tool: write_report
# =========================
def write_report(
    test_name: str,
    status_json: str,
    report_file: str | None = None,
) -> dict:
    """
    Tool: Append a testcase result to test_reports/results.md.

    Parameters:
      - test_name: Short descriptive name (e.g., "Flipkart Add To Cart")
      - status_json: A JSON string with keys:
            {
              "status": "PASS"|"FAIL",
              "checks": [{"name": str, "ok": bool, "details": str}],
              "artifacts": {"url": str, "title": str}
            }
      - report_file (optional): custom path for the markdown report.

    Returns:
      dict: {"ok": bool, "path": str} or {"ok": False, "error": str}
    """
    try:
        ensure_reports_dir()
        generate_test_suites_file()

        if report_file is None:
            report_file = os.path.join(repo_root(), "test_reports", "results.md")

        # Parse input status JSON
        obj = json.loads(status_json)
        status = obj.get("status", "UNKNOWN")
        checks = obj.get("checks", [])
        artifacts = obj.get("artifacts", {})
        url = artifacts.get("url", "")
        title = artifacts.get("title", "")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare markdown block
        lines = [
            f"## {test_name} — {status}\n",
            f"- When: {now}\n",
            f"- URL: {url}\n",
            f"- Title: {title}\n",
            f"- Checks:\n",
        ]
        for c in checks:
            ok = bool(c.get("ok"))
            nm = c.get("name", "")
            det = c.get("details", "")
            lines.append(f"  - [{'✓' if ok else '✗'}] {nm} — {det}\n")
        lines.append("\n---\n\n")

        with open(report_file, "a", encoding="utf-8") as f:
            f.writelines(lines)

        return {"ok": True, "path": report_file}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# =========================
# Agent Instruction
# =========================
INSTRUCTIONS = """
You are a browser automation agent.

You MUST use Playwright MCP tools to:
- open URLs
- click elements
- type into inputs
- extract text
- evaluate code in the page

Rules:
- Never call any tool that installs browsers (e.g., browser_install). The MCP server is already configured to use Microsoft Edge on this machine.
- Do NOT explain actions.
- ONLY return results produced by tool calls.

FINALIZATION REQUIREMENT:
1) After executing all steps and validations, you MUST prepare a JSON object with this EXACT schema:

{
  "status": "PASS" | "FAIL",
  "checks": [
    { "name": string, "ok": boolean, "details": string }
  ],
  "artifacts": {
    "url": string,
    "title": string
  }
}

2) Make a final call to the tool `write_report` with:
   - test_name: a short descriptive name (e.g., "Flipkart Add To Cart")
   - status_json: the JSON string above
   - (optional) report_file: omit to use the default test_reports/results.md

Return ONLY tool outputs.
"""

# =========================
# Root Agent
# =========================
root_agent = LlmAgent(
    model=openai_llm,           # pass the model object
    name="root_agent",
    description="Browser automation agent using Playwright MCP that writes a Markdown test report",
    instruction=INSTRUCTIONS,
    tools=[
        playwright_mcp,   # MCP toolset for browser automation (SSE transport)
        write_report,     # local tool
    ],
)



import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

A2A_PORT = int(os.getenv("A2A_PORT", "8001"))
A2A_HOST = os.getenv("A2A_HOST", "0.0.0.0")

a2a_app = to_a2a(root_agent, port=A2A_PORT)

