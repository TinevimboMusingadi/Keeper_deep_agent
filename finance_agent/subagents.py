"""Subagent definitions for Keeper (ingest) and Clerk (reports)."""

from pathlib import Path
from typing import Optional

from deepagents import CompiledSubAgent, create_deep_agent
from deepagents.backends import FilesystemBackend

from .config import WORKSPACE_ROOT
from .tools import (
    parse_document,
    parse_tabular,
    init_chart_of_accounts,
    post_transactions_from_csv,
    generate_financial_reports,
)

KEEPER_PROMPT = """
You are Keeper, a finance ingestion specialist.
- Always operate inside the workspace filesystem.
- Expected inputs: absolute file paths to PDFs/CSVs/TXT/MD plus brief instructions.
- Use parse_document for PDFs/TXT/MD. Use parse_tabular for CSV/TSV to preview headers and sample rows.
- Persist outputs:
  - Write extracted text or CSV preview to /ingest/keeper_text.txt (append if multiple files).
  - If transactions CSV exists, keep it at /ingest/transactions.csv (or a clearly named file) for Clerk.
  - Write a short log to /logs/keeper.log describing what was parsed.
- If file is unsupported or empty, write a note to /logs/keeper.log and return a concise error.
- Do not produce final finance statements; only ingestion and normalization.
"""

CLERK_PROMPT = """
You are Clerk, a finance reporting specialist.
- Inputs: normalized text or CSV paths produced by Keeper (under /ingest).
- Tasks: organize transactions, draft trial balance or simple summaries.
- Tools:
  - init_chart_of_accounts to create a default CoA if none exists.
  - post_transactions_from_csv to build a journal from CSV (debit_code, credit_code, amount).
  - generate_financial_reports to emit trial balance, income statement, balance sheet.
- Use read_file/glob/grep to locate data.
- Persist outputs:
  - Write interim notes to /logs/clerk.log.
  - Write report drafts to /reports/*.md (balance_sheet.md, income_statement.md, trial_balance.md).
- Keep responses concise; avoid repeating raw documents.
"""


def _build_backend(shared_backend: Optional[FilesystemBackend]) -> FilesystemBackend:
    if shared_backend:
        return shared_backend
    return FilesystemBackend(root_dir=str(WORKSPACE_ROOT))


def build_keeper_subagent(model: str, backend: Optional[FilesystemBackend] = None) -> CompiledSubAgent:
    backend = _build_backend(backend)
    keeper_agent = create_deep_agent(
        model=model,
        backend=backend,
        tools=[parse_document, parse_tabular],
        system_prompt=KEEPER_PROMPT,
    )
    return CompiledSubAgent(
        name="keeper",
        description="Ingests finance docs (PDF/CSV/TXT/MD), extracts text, logs results.",
        runnable=keeper_agent,
    )


def build_clerk_subagent(model: str, backend: Optional[FilesystemBackend] = None) -> CompiledSubAgent:
    backend = _build_backend(backend)
    clerk_agent = create_deep_agent(
        model=model,
        backend=backend,
        tools=[init_chart_of_accounts, post_transactions_from_csv, generate_financial_reports],
        system_prompt=CLERK_PROMPT,
    )
    return CompiledSubAgent(
        name="clerk",
        description="Prepares finance summaries/reports from ingested data; writes to /reports.",
        runnable=clerk_agent,
    )


