from .symbolic import AccountSymbol, TransactionSymbol, AccountType
from .ledger import ChartOfAccounts
from .engine import GeneralJournal, ComputationalEngine

class PeriodEndCloser:
    """
    Handles the procedure for closing temporary accounts at the end of an accounting period.
    """
    def __init__(self, journal: GeneralJournal, coa: ChartOfAccounts, retained_earnings_account: AccountSymbol):
        """
        Initializes the closer.

        Args:
            journal: The GeneralJournal containing the period's transactions.
            coa: The Chart of Accounts.
            retained_earnings_account: The permanent equity account to which net income will be closed.
        
        Raises:
            ValueError: If the target account is not an Equity account.
        """
        if retained_earnings_account.account_type != AccountType.EQUITY:
            raise ValueError("The closing account must be of type Equity (e.g., Retained Earnings).")

        self.journal = journal
        self.coa = coa
        self.retained_earnings_account = retained_earnings_account

    def run_closing_entries(self):
        """
        Calculates balances for all temporary accounts (Revenue and Expense) and
        posts journal entries to close them to Retained Earnings.
        """
        # First, compute the current balances to determine what needs to be closed.
        engine = ComputationalEngine(self.journal)
        engine.compute_balances()

        # Close all revenue accounts
        for account in self.coa:
            if account.account_type == AccountType.REVENUE:
                balance = engine.get_balance(account.name)
                if balance != 0:
                    # Revenue has a credit balance (negative). To close, debit the revenue account.
                    closing_txn = TransactionSymbol(
                        debit=account,
                        credit=self.retained_earnings_account,
                        amount=abs(balance)
                    )
                    self.journal.record_entry(closing_txn)

        # Close all expense accounts
        for account in self.coa:
            if account.account_type == AccountType.EXPENSE:
                balance = engine.get_balance(account.name)
                if balance != 0:
                    # Expense has a debit balance (positive). To close, credit the expense account.
                    closing_txn = TransactionSymbol(
                        debit=self.retained_earnings_account,
                        credit=account,
                        amount=balance
                    )
                    self.journal.record_entry(closing_txn) 