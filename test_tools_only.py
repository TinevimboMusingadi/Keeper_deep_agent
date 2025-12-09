"""Test finance tools without requiring deepagents."""
import sys
from pathlib import Path

# Add custom_tool_examples to path
sys.path.insert(0, str(Path(__file__).parent))

from custom_tool_examples.symbolic import AccountType
from custom_tool_examples.ledger import ChartOfAccounts
from custom_tool_examples.engine import GeneralJournal, ComputationalEngine
from custom_tool_examples.reports import FinancialReporter
import json

print("Testing Finance Tools (Symbolic Accounting Engine)...")
print("=" * 60)

# Create workspace
workspace = Path("finance_agent_workspace")
workspace.mkdir(exist_ok=True)
(workspace / "reports").mkdir(exist_ok=True)
(workspace / "ingest").mkdir(exist_ok=True)

print(f"Workspace: {workspace.absolute()}")

# 1. Create Chart of Accounts
print("\n1. Creating Chart of Accounts...")
coa = ChartOfAccounts()

# Assets
coa.add_account("1010", "Cash", AccountType.ASSET)
coa.add_account("1020", "Accounts Receivable", AccountType.ASSET)

# Liabilities
coa.add_account("2010", "Accounts Payable", AccountType.LIABILITY)

# Equity
coa.add_account("3010", "Retained Earnings", AccountType.EQUITY)

# Revenue
coa.add_account("4000", "Sales Revenue", AccountType.REVENUE)

# Expenses
coa.add_account("5000", "Operating Expenses", AccountType.EXPENSE)

coa_path = workspace / "reports" / "chart_of_accounts.json"
coa.save(str(coa_path))
print(f"✓ Chart of Accounts saved: {coa_path}")
print(f"  Accounts created: {len(coa)}")

# 2. Create sample transactions
print("\n2. Creating sample transactions...")
journal = GeneralJournal(coa)

# Sample transaction: Sale (Debit Cash, Credit Sales Revenue)
from custom_tool_examples.symbolic import TransactionSymbol
cash = coa.get_account("1010")
sales = coa.get_account("4000")
expenses = coa.get_account("5000")
payable = coa.get_account("2010")

# Transaction 1: Sale of $1000
txn1 = TransactionSymbol(debit=cash, credit=sales, amount=1000.0)
journal.record_entry(txn1)
print(f"✓ Recorded: Sale of $1000 (Cash +$1000, Sales Revenue +$1000)")

# Transaction 2: Expense of $500
txn2 = TransactionSymbol(debit=expenses, credit=cash, amount=500.0)
journal.record_entry(txn2)
print(f"✓ Recorded: Expense of $500 (Operating Expenses +$500, Cash -$500)")

journal_path = workspace / "reports" / "general_journal.json"
journal.save(str(journal_path))
print(f"✓ Journal saved: {journal_path}")
print(f"  Total entries: {len(journal)}")

# 3. Compute balances
print("\n3. Computing account balances...")
engine = ComputationalEngine(journal)
engine.compute_balances()

print("Account Balances:")
for account in coa:
    balance = engine.get_balance(account.name)
    if balance != 0:
        print(f"  {account.code} {account.name}: ${balance:,.2f}")

trial_balance = engine.trial_balance()
print(f"\n✓ Trial Balance: ${trial_balance:.2f} (should be ~0)")

# 4. Generate reports
print("\n4. Generating financial reports...")
reporter = FinancialReporter(engine, coa)

# Trial Balance
tb_rows = reporter.generate_trial_balance()
tb_path = workspace / "reports" / "trial_balance.md"
with open(tb_path, 'w', encoding='utf-8') as f:
    f.write("# Trial Balance\n\n")
    f.write("| Code | Account | Debit | Credit |\n")
    f.write("|------|---------|-------|--------|\n")
    for code, name, debit, credit in tb_rows:
        f.write(f"| {code} | {name} | ${debit:,.2f} | ${credit:,.2f} |\n")
print(f"✓ Trial Balance: {tb_path}")

# Income Statement
income_data, net_income = reporter.generate_income_statement()
income_path = workspace / "reports" / "income_statement.md"
with open(income_path, 'w', encoding='utf-8') as f:
    f.write("# Income Statement\n\n")
    f.write("## Revenue\n")
    total_rev = 0
    for item in income_data:
        if item['amount'] > 0:
            f.write(f"- {item['category']}: ${item['amount']:,.2f}\n")
            total_rev += item['amount']
    f.write(f"\n**Total Revenue**: ${total_rev:,.2f}\n\n")
    f.write("## Expenses\n")
    total_exp = 0
    for item in income_data:
        if item['amount'] < 0:
            f.write(f"- {item['category']}: ${abs(item['amount']):,.2f}\n")
            total_exp += abs(item['amount'])
    f.write(f"\n**Total Expenses**: ${total_exp:,.2f}\n\n")
    f.write(f"## Net Income: ${net_income:,.2f}\n")
print(f"✓ Income Statement: {income_path}")
print(f"  Net Income: ${net_income:,.2f}")

# Balance Sheet
bs_totals, is_balanced = reporter.generate_balance_sheet()
bs_path = workspace / "reports" / "balance_sheet.md"
with open(bs_path, 'w', encoding='utf-8') as f:
    f.write("# Balance Sheet\n\n")
    f.write("## Assets\n")
    f.write(f"- Total Assets: ${bs_totals['Assets']:,.2f}\n\n")
    f.write("## Liabilities\n")
    f.write(f"- Total Liabilities: ${bs_totals['Liabilities']:,.2f}\n\n")
    f.write("## Equity\n")
    f.write(f"- Total Equity: ${bs_totals['Equity']:,.2f}\n\n")
    f.write(f"**Total Liabilities + Equity**: ${bs_totals['Liabilities'] + bs_totals['Equity']:,.2f}\n")
    f.write(f"\n**Balanced**: {'✓ Yes' if is_balanced else '✗ No'}\n")
print(f"✓ Balance Sheet: {bs_path}")
print(f"  Assets: ${bs_totals['Assets']:,.2f}")
print(f"  Liabilities: ${bs_totals['Liabilities']:,.2f}")
print(f"  Equity: ${bs_totals['Equity']:,.2f}")
print(f"  Balanced: {'✓' if is_balanced else '✗'}")

print("\n" + "=" * 60)
print("✓ All tests completed successfully!")
print(f"\nReports saved to: {workspace.absolute() / 'reports'}")
