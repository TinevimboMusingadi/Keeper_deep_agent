"""Custom tools for the finance deep agent."""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from langchain_core.tools import tool

from custom_tool_examples.document_parser import get_file_content_as_text, DocumentReadError
from custom_tool_examples.ledger import ChartOfAccounts
from custom_tool_examples.engine import GeneralJournal, ComputationalEngine
from custom_tool_examples.reports import FinancialReporter
from custom_tool_examples.symbolic import AccountType, TransactionSymbol

log = logging.getLogger(__name__)


@tool
async def parse_document(file_path: str) -> Dict[str, Any]:
    """
    Parse a finance document (PDF/TXT/MD) into text.

    Expects an absolute path within the agent's filesystem backend.
    Returns dict with keys: status, text_content?, file_type?, message?
    """
    path = Path(file_path)
    if not path.is_absolute():
        raise ValueError("file_path must be an absolute path inside the agent workspace.")

    result = await get_file_content_as_text(str(path))
    status = result.get("status")
    if status != "success":
        msg = result.get("message", "Unknown parse error")
        raise DocumentReadError(msg)

    log.info(
        "Parsed document %s (type=%s, len=%s)",
        path,
        result.get("file_type"),
        len(result.get("text_content", "")),
    )
    return result


@tool
async def parse_tabular(file_path: str, max_rows: int = 20) -> Dict[str, Any]:
    """
    Parse CSV/TSV into a structured preview (columns, row count, head sample).
    """
    path = Path(file_path)
    if not path.is_absolute():
        raise ValueError("file_path must be absolute inside the workspace.")
    if not path.exists():
        raise FileNotFoundError(f"{file_path} not found.")

    delimiter = "," if path.suffix.lower() == ".csv" else "\t"
    rows: List[List[str]] = []
    header: List[str] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for idx, row in enumerate(reader):
            if idx == 0:
                header = row
                continue
            rows.append(row)
            if len(rows) >= max_rows:
                break
    return {
        "status": "success",
        "file": str(path),
        "header": header,
        "rows_preview": rows,
    }


def _default_accounts() -> List[tuple]:
    return [
        ("1000", "Cash", AccountType.ASSET),
        ("1100", "Accounts Receivable", AccountType.ASSET),
        ("2000", "Accounts Payable", AccountType.LIABILITY),
        ("3000", "Retained Earnings", AccountType.EQUITY),
        ("4000", "Revenue", AccountType.REVENUE),
        ("5000", "Expenses", AccountType.EXPENSE),
    ]


@tool
def init_chart_of_accounts(output_path: str = "/reports/chart_of_accounts.json") -> Dict[str, Any]:
    """
    Create a default Chart of Accounts JSON file.
    """
    path = Path(output_path)
    if not path.is_absolute():
        raise ValueError("output_path must be absolute.")
    path.parent.mkdir(parents=True, exist_ok=True)

    coa = ChartOfAccounts()
    for code, name, atype in _default_accounts():
        coa.add_account(code=code, name=name, account_type=atype)
    coa.save(str(path))
    return {"status": "success", "chart_path": str(path)}


def _load_coa(path: Path) -> ChartOfAccounts:
    if not path.exists():
        raise FileNotFoundError(f"Chart of accounts not found: {path}")
    return ChartOfAccounts.load(str(path))


@tool
def post_transactions_from_csv(csv_path: str, coa_path: str, journal_path: str = "/reports/journal.json") -> Dict[str, Any]:
    """
    Read transactions from CSV (columns: debit_code, credit_code, amount) and persist journal.
    """
    csv_p = Path(csv_path)
    coa_p = Path(coa_path)
    journal_p = Path(journal_path)
    for p in (csv_p, coa_p, journal_p):
        if not p.is_absolute():
            raise ValueError("All paths must be absolute.")
    if not csv_p.exists():
        raise FileNotFoundError(f"CSV not found: {csv_p}")

    coa = _load_coa(coa_p)
    journal = GeneralJournal(coa)

    with csv_p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            debit_code = row.get("debit_code") or row.get("debit") or row.get("debit_account")
            credit_code = row.get("credit_code") or row.get("credit") or row.get("credit_account")
            amount_val = row.get("amount")
            if not debit_code or not credit_code or amount_val is None:
                continue
            amount = float(amount_val)
            debit_acc = coa.get_account(debit_code)
            credit_acc = coa.get_account(credit_code)
            txn = TransactionSymbol(debit=debit_acc, credit=credit_acc, amount=amount)
            journal.record_entry(txn)

    journal_p.parent.mkdir(parents=True, exist_ok=True)
    journal.save(str(journal_p))
    return {"status": "success", "journal_path": str(journal_p), "entries": len(journal)}


def _load_journal(journal_path: Path, coa: ChartOfAccounts) -> GeneralJournal:
    journal = GeneralJournal(coa)
    journal.load(str(journal_path))
    return journal


@tool
def generate_financial_reports(coa_path: str, journal_path: str, output_dir: str = "/reports") -> Dict[str, Any]:
    """
    Generate trial balance, income statement, and balance sheet markdown files.
    """
    coa_p = Path(coa_path)
    journal_p = Path(journal_path)
    out_dir = Path(output_dir)
    for p in (coa_p, journal_p, out_dir):
        if not p.is_absolute():
            raise ValueError("Paths must be absolute.")
    out_dir.mkdir(parents=True, exist_ok=True)

    coa = _load_coa(coa_p)
    journal = _load_journal(journal_p, coa)
    engine = ComputationalEngine(journal)
    engine.compute_balances()
    reporter = FinancialReporter(engine, coa)

    trial = reporter.generate_trial_balance()
    income, net_income = reporter.generate_income_statement()
    balance, balanced = reporter.generate_balance_sheet()

    tb_md = ["# Trial Balance", "| Code | Account | Debit | Credit |", "|---|---|---|---|"]
    for code, name, debit, credit in trial:
        tb_md.append(f"| {code} | {name} | {debit:.2f} | {credit:.2f} |")

    inc_md = ["# Income Statement", "| Category | Amount |", "|---|---|"]
    for row in income:
        inc_md.append(f"| {row['category']} | {row['amount']:.2f} |")
    inc_md.append(f"\n**Net Income:** {net_income:.2f}")

    bal_md = ["# Balance Sheet", "| Category | Total |", "|---|---|"]
    for k, v in balance.items():
        bal_md.append(f"| {k} | {v:.2f} |")
    bal_md.append(f"\n**Balanced:** {balanced}")

    tb_path = out_dir / "trial_balance.md"
    inc_path = out_dir / "income_statement.md"
    bal_path = out_dir / "balance_sheet.md"

    tb_path.write_text("\n".join(tb_md), encoding="utf-8")
    inc_path.write_text("\n".join(inc_md), encoding="utf-8")
    bal_path.write_text("\n".join(bal_md), encoding="utf-8")

    return {
        "status": "success",
        "trial_balance": str(tb_path),
        "income_statement": str(inc_path),
        "balance_sheet": str(bal_path),
        "balanced": balanced,
    }
