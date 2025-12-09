# symbolic_accounting/engine.py
from collections import defaultdict
from typing import List
from .symbolic import TransactionSymbol, AccountType, AccountSymbol
from .ledger import ChartOfAccounts
import json

class GeneralJournal:
    """
    Represents the 'book of original entry' where all symbolic transactions
    (journal entries) are formally recorded.
    
    It validates every transaction against a Chart of Accounts to ensure
    that only legitimate accounts are used.
    """
    def __init__(self, coa: ChartOfAccounts):
        self.coa = coa
        self.entries: List[TransactionSymbol] = []

    def record_entry(self, txn: TransactionSymbol):
        """
        Records a new transaction after validating its accounts.
        
        Args:
            txn: The TransactionSymbol to record.
            
        Raises:
            KeyError: If the debit or credit account in the transaction
                      does not exist in the Chart of Accounts.
        """
        # Throws KeyError if account doesn't exist, providing validation
        self.coa.get_account(txn.debit.name)
        self.coa.get_account(txn.credit.name)
        self.entries.append(txn)

    def __len__(self):
        return len(self.entries)

    def save(self, filepath: str):
        """Saves the journal's entries to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump([entry.to_dict() for entry in self.entries], f, indent=2)

    def load(self, filepath: str):
        """
        Loads journal entries from a JSON file.
        
        This assumes the ChartOfAccounts has already been loaded.
        """
        with open(filepath, 'r') as f:
            entries_data = json.load(f)
            
        self.entries = [] # Clear existing entries before loading
        for entry_data in entries_data:
            debit_acc = self.coa.get_account(entry_data['debit_code'])
            credit_acc = self.coa.get_account(entry_data['credit_code'])
            
            self.record_entry(
                TransactionSymbol(
                    debit=debit_acc,
                    credit=credit_acc,
                    amount=entry_data['amount']
                )
            )

class ComputationalEngine:
    """
    Processes a list of symbolic transactions to compute numeric balances.
    It understands the rules of debit and credit for all account types.
    """
    def __init__(self, journal: GeneralJournal):
        self.journal = journal
        self.ledger = defaultdict(float)

    def compute_balances(self):
        """
        Calculates the final balance for each account by processing
        all transactions. Debits are treated as positive values and
        credits as negative values. The final ledger is a sum of
        all these operations, and the trial balance should naturally be zero.
        """
        self.ledger.clear()
        for txn in self.journal.entries:
            self.ledger[txn.debit.name] += txn.amount
            self.ledger[txn.credit.name] -= txn.amount

    def get_balance(self, account_name: str) -> float:
        """Returns the computed balance for a specific account."""
        return self.ledger.get(account_name, 0.0)

    def trial_balance(self) -> float:
        """
        Calculates the sum of all balances in the ledger. For a correctly
        balanced system, this should be zero (or very close to it, due
        to potential floating-point inaccuracies).
        """
        return sum(self.ledger.values())

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