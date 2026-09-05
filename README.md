# ResolveAI - Customer Support Resolution Assistant

**Problem Statement:** PS04 – Customer Support Resolution Assistant  
**Goal:** Build a grounded AI assistant that helps customer support agents handle routine broadband/mobile customer issues.

---

## Key Features & Request Support

The assistant handles three main categories of requests:
1. **Billing Complaints** (e.g., unexpected charges, payment failures, refund requests)
2. **Connection Problems** (e.g., speed drops, outages, router connectivity issues)
3. **Plan Questions** (e.g., plan upgrades, data caps, roaming options)

---

## Decision Engine Matrix

For every customer query, ResolveAI evaluates verified data and outputs one of three decisions:

- **`RESOLVE`**: Fully answers the customer using verified local account data and support knowledge articles.
- **`ASK`**: Asks for *exact missing information* required to proceed with resolution.
- **`ESCALATE`**: Hands the case over to a human agent when the issue is complex, unsupported, uncertain, or repeatedly unresolved.

---

## Architecture & Principles

- **Grounded AI**: The LLM is strictly prohibited from inventing or hallucinating customer or account facts.
- **Deterministic Business Rules**: Core logic and escalation boundaries are governed by Python rules.
- **Gemini API Integration**: Uses Google Gemini API for natural language understanding, reasoning, and semantic search embeddings.
- **Local Data Storage**: Customer profiles, ticket histories, and support articles are stored locally in `data/`.
- **Evidence & Source Citations**: Every resolution displays verifiable supporting evidence and cited source articles.
- **Single-Command Launch**: Serves backend API and frontend UI on `http://localhost:8000` via standard Python runtime without extra build tools or multi-terminal setups.

---

## Project Structure

```
ResolveAI/
├── app.py                   # Main HTTP server & API endpoint router
├── requirements.txt         # Project dependencies
├── README.md                # Documentation & project overview
├── .gitignore               # Git ignore rules
├── src/
│   ├── init.py              # Package initialization & setup helpers
│   ├── __init__.py          # Python package marker
│   ├── gemini.py            # Gemini API client & reasoning wrapper
│   ├── retrieval.py         # Knowledge base & customer data retriever
│   ├── rules.py             # Deterministic decision rules engine
│   └── support.py           # Core resolution workflow coordinator
├── data/
│   ├── customers.json       # Local customer account records
│   ├── tickets.json         # Local support ticket history
│   └── articles/            # Knowledge base markdown articles
│       ├── billing.md
│       ├── connection.md
│       ├── plans.md
│       └── refunds.md
└── frontend/
    ├── index.html           # Agent dashboard UI structure
    ├── style.css            # UI styling & design tokens
    └── script.js            # Frontend interactivity & API consumer
```

---

## Quick Start

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   PORT=8000
   ```

3. **Run the Application:**
   ```bash
   python app.py
   ```
   Open `http://localhost:8000` in your web browser.

---

## Development Status

- [x] Initial directory structure and module placeholders created.
- [ ] Core backend logic implementation (`app.py`, `src/`).
- [ ] Data files populated with test records (`data/`).
- [ ] UI Dashboard implementation (`frontend/`).
