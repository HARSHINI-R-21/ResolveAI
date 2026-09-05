TRACK_ID=PS6
# ResolveAI

> **"Resolve faster. Escalate smarter."**

**Problem Statement:** PS04 – Customer Support Resolution Assistant

---

## Problem

Customer support agents waste significant time manually searching across customer account details, past ticket histories, and technical documentation while trying to resolve routine broadband and mobile issues.

## Solution

**ResolveAI** is a grounded AI support resolution assistant designed to streamline customer support. It combines local customer records, support ticket history, knowledge base markdown articles, Gemini intent classification, and a **deterministic Python RuleEngine** to deliver grounded resolutions, request missing information, or generate structured human escalation handovers.

---

## Key Features

- **Customer Context Retrieval**: Instant lookup of verified customer profile, billing status, and line status.
- **Ticket History Retrieval**: Automatic tracking of prior support contacts and troubleshooting attempts.
- **Local Knowledge Base Search**: Deterministic local keyword matching across verified markdown support articles.
- **Gemini Intent Detection**: AI-powered classification of customer queries (`BILLING`, `CONNECTION`, `PLAN`, `REFUND`, `OTHER`).
- **Deterministic Decision Engine**: Pure Python business logic governing `RESOLVE`, `ASK`, and `ESCALATE` outcomes.
- **Grounded AI Response Generation**: Strict prompt boundaries ensuring zero hallucinated facts, prices, or policies.
- **Evidence & Citation Display**: Factual bullet points detailing source data and cited KB articles.
- **Escalation Handover Summaries**: Structured summaries highlighting established facts and previous attempts for Level-2 agents.
- **Missing Information Requests**: Explicit identification of required customer details before proceeding.

---

## System Architecture & Decision Flow

```
Customer Message
      ↓
Gemini Intent Classification
      ↓
Local Customer/Ticket/Article Retrieval
      ↓
Python RuleEngine (src/rules.py)
      ↓
RESOLVE / ASK / ESCALATE
      ↓
Grounded Gemini Response Generation
      ↓
Support Dashboard Result
```

The deterministic Python RuleEngine is the authoritative decision layer for RESOLVE, ASK, and ESCALATE outcomes. Gemini handles intent classification and grounded response formatting, but never overrides business decisions.

---

## Tech Stack

- **Backend**: Python (Standard Library HTTP Server)
- **Frontend**: HTML5, Vanilla CSS3 (Dark SaaS Dashboard), Vanilla JavaScript (ES6)
- **AI Integration**: Google Gemini API (`google-genai`)
- **Data Storage**: Local JSON records (`customers.json`, `tickets.json`) & Markdown articles (`data/articles/*.md`)
- **Infrastructure**: Zero external database dependencies; no hosted vector database required.

---

## API Endpoints

The frontend and backend are served together from port 8000 (e.g. `http://localhost:8000`).

- `GET /` — Serves the single-page agent dashboard UI.
- `GET /api/customers` — Returns all verified customer account records.
- `GET /api/customers/{customer_id}` — Returns profile details for a specific customer ID.
- `POST /api/resolve` — Accepts customer query payload and executes the resolution pipeline.

---

## Project Structure

```
ResolveAI/
├── app.py                   # Main HTTP server & API router
├── requirements.txt         # Dependencies (google-genai, python-dotenv)
├── README.md                # Project documentation & evaluator guide
├── .gitignore               # Excludes virtual environments, secrets, logs
├── src/
│   ├── init.py              # Environment verification helper
│   ├── __init__.py          # Python package marker
│   ├── gemini.py            # Gemini client wrapper (Intent & Grounded Response)
│   ├── retrieval.py         # Deterministic data loader & article search
│   ├── rules.py             # Deterministic decision RuleEngine (Authoritative)
│   └── support.py           # Resolution pipeline coordinator
├── data/
│   ├── customers.json       # Verified customer profiles (C001 - C010)
│   ├── tickets.json         # Support ticket history & troubleshooting logs
│   └── articles/            # Grounded knowledge base articles
│       ├── billing.md       # BILL-001: Unexpected Bill Increase
│       ├── connection.md    # CONN-001: Internet Connection Troubleshooting
│       ├── plans.md         # PLAN-001: Plan Upgrade
│       └── refunds.md       # REFUND-001: Credits and Refunds
└── frontend/
    ├── index.html           # Agent dashboard single-page interface
    ├── style.css            # SaaS design tokens, badges, and layout
    └── script.js            # Interactivity, dropdown loader & API consumer
```

---

## Quick Setup & Run

No complex build steps, node processes, or multi-terminal setups required.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HARSHINI-R-21/ResolveAI.git
   cd ResolveAI
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Gemini API Key (Optional):**
   Create a `.env` file in the root directory (or export environment variable):
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```
   *(Note: If `GEMINI_API_KEY` is omitted, ResolveAI operates safely in deterministic fallback mode.)*

5. **Start the application:**
   ```bash
   python app.py
   ```

6. **Access the Dashboard:**
   Open your web browser at `http://localhost:8000`.

---

## Hackathon Demo Scenarios

Evaluators can test these pre-configured scenarios in the agent dashboard:

### 1. DEMO 1 — RESOLVE
- **Customer:** `C001 - Alice Smith`
- **Query:** `"Why is my bill higher this month?"`
- **Intent:** `BILLING`
- **Decision:** **`RESOLVE`**
- **Knowledge Source:** `BILL-001` (*Unexpected Bill Increase*)
- **Outcome:** Answers using verified account data (Plan: BasicFiber 100, Current Bill: $49.99, Billing Status: paid) and marks response *"✓ Ready for agent review"*.

### 2. DEMO 2 — ASK
- **Customer:** `C004 - Diana Prince`
- **Query:** `"I want to upgrade my plan."`
- **Intent:** `PLAN`
- **Decision:** **`ASK`**
- **Knowledge Source:** `PLAN-001` (*Plan Upgrade*)
- **Outcome:** Displays **"Additional Information Needed"** panel asking specifically for missing target speed & usage preferences.

### 3. DEMO 3 — ESCALATE (Key Escalation Demo)
- **Customer:** `C005 - Ethan Vance`
- **Query:** `"My internet has been down for 3 days. I already contacted support twice."`
- **Intent:** `CONNECTION`
- **Decision:** **`ESCALATE`**
- **Knowledge Source:** `CONN-001` (*Internet Connection Troubleshooting*)
- **Outcome:** Renders structured **"Escalation Handover Summary"** detailing `ESTABLISHED FACTS` (inactive connection, paid status, 2 open tickets) and `PREVIOUS ATTEMPTS` (`["router restart", "remote ONT power cycle", ...]`).

---

## Grounding & Safety Guarantees

- **Zero Fact Fabrication**: AI responses are bounded strictly by verified local customer records, ticket logs, and Markdown articles.
- **Authoritative Business Rules**: Logic branches and escalation limits are enforced deterministically in Python (`src/rules.py`).
- **No Client API Keys**: `GEMINI_API_KEY` is kept strictly on the backend; no API keys, tokens, or secrets are exposed to frontend JavaScript or browser network calls.
- **Graceful Fallback Handling**: If Gemini is unavailable or rate-limited, the system safely serves deterministic fallback evidence without crashing.
