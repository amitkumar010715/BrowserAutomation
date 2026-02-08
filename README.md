# Browser Automation Agent

This repository contains a browser automation agent built using Playwright MCP over HTTP/SSE. The agent is designed to execute natural-language test cases and generate a PASS/FAIL summary in a Markdown report.

## Features
- **Browser Automation**: Uses Playwright MCP for browser interactions such as opening URLs, clicking elements, typing into inputs, extracting text, and evaluating code on web pages.
- **Test Reporting**: Generates Markdown reports summarizing test results.
- **A2A Integration**: Converts the agent into an A2A-ready FastAPI app with an auto-generated Agent Card.

## Setup

### Prerequisites
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install Playwright MCP:
   ```bash
   npx @playwright/mcp@latest --port 8931 --executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
   ```

### Environment Variables
Create a `.env` file in the root directory with the following variables:
```
OPENAI_API_KEY=<your_openai_api_key>
OPENAI_MODEL=openai/gpt-4o-mini
PLAYWRIGHT_MCP_SSE_URL=http://localhost:8931/sse
A2A_PORT=8001
A2A_HOST=0.0.0.0
```

## Usage

### Running the Agent
1. Start the Playwright MCP server:
   ```bash
   npx @playwright/mcp@latest --port 8931 --executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
   ```
2. Run the agent:
   ```bash
   adk run my_agent
   ```
3. Provide natural-language instructions, e.g.,
   ```
   goto flipkart site, close the login pop-up, search for t-shirt, select first one, add to cart.
   ```

### Running as an A2A App
1. Navigate to the `my_agent` directory:
   ```bash
   cd my_agent
   ```
2. Start the FastAPI app:
   ```bash
   uvicorn agent:a2a_app --host localhost --port 8001
   ```
3. Access the Agent Card at:
   [http://127.0.0.1:8001/.well-known/agent-card.json](http://127.0.0.1:8001/.well-known/agent-card.json)

## File Structure
```
new_litellm/
├── requirements.txt
├── my_agent/
│   ├── __init__.py
│   ├── agent.py
│   └── __pycache__/
```

## Test Reporting
- Test results are written to `test_reports/results.md`.
- Ensure the `test_reports` directory exists before running tests.

## License
This project is licensed under the MIT License.#

