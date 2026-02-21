# CashFlow.ai

> **AI-powered cash flow statement generator for small businesses.**
> Upload any bank export or transaction CSV/Excel — AI normalizes the data, then produces a Direct Method cash flow statement automatically.

---

## What It Does

CashFlow.ai takes raw, messy financial data (bank statements, transaction exports, income/expense spreadsheets) and turns it into a structured **Direct Method Cash Flow Statement** using a two-agent AI pipeline:

1. **Agent 1 — Data Normalizer**: An LLM inspects your file's columns and a sample of rows, then infers a `NormalizationSpec` — a structured set of rules describing how to map your custom columns to a canonical schema (`date`, `description`, `amount`, `direction`, `category`, `balance`, `source`).

2. **Deterministic Transform**: The inferred spec is applied using pure Python/Pandas logic — no second LLM call. This keeps the transform fast, auditable, and reproducible.

3. **Agent 2 — Cash Flow Generator**: The cleaned, normalized data is sent to a second LLM call that produces a clean Markdown Direct Method Cash Flow Statement with inflows, outflows, net change, and an optional balance reconciliation check.

The separation of LLM inference from deterministic execution means you can debug, cache, and reuse the normalization rules independently of the cash flow generation step.

---

## Architecture

```
Uploaded CSV / Excel
        │
        ▼
┌───────────────────────┐
│  Agent 1 (LLM)        │  ← inspects headers + 40 sample rows
│  Data Normalizer      │  ← outputs NormalizationSpec (Pydantic)
└───────────┬───────────┘
            │ spec (cached per file signature)
            ▼
┌───────────────────────┐
│  Deterministic        │  ← apply_spec() — pure Pandas
│  Transformer          │  ← handles signed, debit/credit, type-flag layouts
└───────────┬───────────┘
            │ normalized_df  +  quality issues
            ▼
┌───────────────────────┐
│  Agent 2 (LLM)        │  ← receives normalized CSV
│  Cash Flow Generator  │  ← outputs Direct Method statement (Markdown)
└───────────────────────┘
```

---

## Features

- Handles any column naming convention — `Date`, `Txn Date`, `Trans. Date`, `VALUE DATE`, etc.
- Supports three amount layouts: **signed amount**, **debit/credit split**, **type-flag column**
- Caches the inferred spec per file (by header hash) — no LLM call on re-upload
- Quality checks: duplicate column detection, unparseable date reporting, both-debit-and-credit warnings
- Export normalized data as CSV
- Streamlit UI — no coding required to use

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | OpenAI GPT-4o-mini (via LangChain) |
| Schema validation | Pydantic v2 |
| Data processing | Pandas |
| Async execution | Python asyncio |

---

## Project Structure

```
src/
├── streamlit_app.py              # Main UI entrypoint
├── agents/
│   ├── cashflow_agent.py         # Agent 2: cash flow generation
│   ├── data_normalizer_agent.py  # Agent 1: LLM spec inference
│   └── base_agent.py             # Base class (WIP)
├── core/
│   ├── settings.py               # Model config, API key loading
│   ├── spec_apply.py             # Deterministic transformer
│   └── llm_normalizer_prompt.py  # Prompts for Agent 1
└── schema/
    ├── normalization_spec_v1.py  # Pydantic spec model
    └── cashflow_direct_v1.py     # Canonical column definitions
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- An OpenAI API key

### Install

```bash
git clone https://github.com/your-username/CashFlow.ai.git
cd CashFlow.ai
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

### Run

```bash
streamlit run src/streamlit_app.py
```

---

## Usage

1. Upload a CSV or Excel file containing financial transactions.
2. Click **Infer Rules & Normalize** — Agent 1 will inspect the data and generate normalization rules.
3. Review the normalized data and any quality warnings.
4. Click **Generate Cash Flow** — Agent 2 will produce a Direct Method statement.
5. Download the normalized CSV if needed.

Use **Reset Rules** to force a fresh LLM inference if your file structure changes.

---

## Learning Goals

This is a learning project exploring:

- Multi-agent AI architectures with clear separation of concerns
- Structured LLM output with Pydantic schema enforcement
- Hybrid AI + deterministic pipelines for reliability and auditability
- Building financial tools with LangChain and Streamlit

---

## Roadmap

- [ ] Agent 3: Reviewer / validator agent that cross-checks the generated statement
- [ ] Indirect Method cash flow support
- [ ] Multi-file consolidation
- [ ] LangGraph-based agent orchestration
- [ ] Support for local LLMs (Ollama)

---

## License

MIT
