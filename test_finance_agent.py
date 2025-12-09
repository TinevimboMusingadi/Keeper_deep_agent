"""Test script for finance agent tools."""
from pathlib import Path
from finance_agent.config import ensure_workspace
from finance_agent.tools import init_chart_of_accounts, post_transactions_from_csv, generate_financial_reports

print("Testing Finance Agent Tools...")
print("=" * 50)

# Setup workspace
root = ensure_workspace()
print(f"Workspace root: {root}")

# Copy sample transactions CSV
src = Path('finance_agent/examples/transactions.csv')
dst = root / 'ingest' / 'transactions.csv'
dst.parent.mkdir(parents=True, exist_ok=True)

if src.exists():
    dst.write_text(src.read_text(), encoding='utf-8')
    print(f"✓ Copied sample CSV to {dst}")
else:
    print(f"⚠ Sample CSV not found at {src}")
    # Create a minimal test CSV
    test_csv = """debit_code,credit_code,amount,description
1010,4000,1000.00,Test Sale
5000,1010,500.00,Test Expense"""
    dst.write_text(test_csv, encoding='utf-8')
    print(f"✓ Created test CSV at {dst}")

# Initialize Chart of Accounts
print("\n1. Initializing Chart of Accounts...")
coa_path = str(root / 'reports' / 'chart_of_accounts.json')
coa_result = init_chart_of_accounts(coa_path)
print(f"✓ Chart of Accounts created: {coa_result['chart_path']}")

# Post transactions from CSV
print("\n2. Posting transactions from CSV...")
journal_result = post_transactions_from_csv(str(dst), coa_result['chart_path'])
print(f"✓ Journal created: {journal_result['journal_path']}")
print(f"  Transactions posted: {journal_result['transaction_count']}")

# Generate financial reports
print("\n3. Generating financial reports...")
reports_result = generate_financial_reports(
    coa_result['chart_path'],
    journal_result['journal_path'],
    str(root / 'reports')
)
print(f"✓ Reports generated:")
for report_type, report_path in reports_result.items():
    if report_path:
        print(f"  - {report_type}: {report_path}")

print("\n" + "=" * 50)
print("Test completed successfully!")
print(f"\nAll files saved to: {root}")
