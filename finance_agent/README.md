# Deep Finance Agent (Harness + Subagents)

This harness uses `deepagents` to orchestrate a finance workflow with three roles:

- **Root (Orchestrator)**: plans, delegates, synthesizes.
- **Keeper (Subagent)**: ingests PDFs/CSVs/TXT/MD using `parse_document`/`parse_tabular`, writes logs/text/ingest files.
- **Clerk (Subagent)**: builds journal + reports from Keeper CSVs using `init_chart_of_accounts`, `post_transactions_from_csv`, `generate_financial_reports`, writes to `/reports`.

## Layout
- `agent.py` – root agent wiring, shared filesystem backend.
- `subagents.py` – Keeper/Clerk definitions and prompts.
- `tools.py` – custom tools (document parser wrapper; ledger placeholder).
- `config.py` – defaults for model and workspace root.
- `main.py` – example runner.

Workspace directories (auto-created): `./finance_agent_workspace/{ingest,reports,logs}`. Override via `FINANCE_AGENT_ROOT` env var.

## Running
```bash
# install dependencies (ensure deepagents + custom_tool_examples deps like pdfplumber)
uv run python -m finance_agent.main
```

### LangGraph server
```bash
# from repo root (langgraph.json points to finance agent)
langgraph dev
```
Assistant ID: `finance`
Deployment URL: shown in terminal (e.g., http://127.0.0.1:2024). You can connect `deep-agents-ui` to this.

Environment knobs:
- `FINANCE_AGENT_MODEL` (default `claude-sonnet-4-5-20250929`)
- `FINANCE_AGENT_ROOT` (workspace path)

## How it works
- Root uses `task()` to delegate ingestion to Keeper, then reporting to Clerk.
- Keeper uses `parse_document` (PDF/TXT/MD) and `parse_tabular` (CSV preview) and writes outputs to `/ingest` plus logs.
- Clerk creates a default CoA (`init_chart_of_accounts`), posts transactions from CSV (`post_transactions_from_csv` with columns debit_code, credit_code, amount), then generates reports (`generate_financial_reports`) to `/reports`.
- Files persist in the shared FilesystemBackend so Root can read reports after subagents finish.

## Example workflow
1) Place `transactions.csv` under `/ingest` with headers: `debit_code,credit_code,amount` (see `finance_agent/examples/transactions.csv`).
2) Root delegates:
   - Keeper: parse docs/CSVs (stores under `/ingest`, logs under `/logs`).
   - Clerk: `init_chart_of_accounts` → `post_transactions_from_csv` → `generate_financial_reports`.
3) Root reads `/reports/*.md` and summarizes locations/results.

## Next steps
- Expand Keeper to normalize invoices → transaction CSVs automatically.
- Add richer CoA loading from user-provided files.
- Expose via LangGraph server and connect `deep-agents-ui` for web UI.


