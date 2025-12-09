# symbolic_accounting/journals.py
from .symbolic import AccountSymbol, TransactionSymbol, AccountType
from .engine import GeneralJournal

class SalesJournal:
    """
    A specialized journal for recording credit sales transactions.
    
    This journal simplifies the process by automatically debiting an
    accounts receivable account and crediting a sales revenue account.
    """
    def __init__(self, general_journal: GeneralJournal, accounts_receivable: AccountSymbol, sales_revenue: AccountSymbol):
        """
        Initializes the SalesJournal.
        
        Args:
            general_journal: The main GeneralJournal where all entries will be posted.
            accounts_receivable: The default 'Accounts Receivable' account to be debited.
            sales_revenue: The default 'Sales Revenue' account to be credited.
            
        Raises:
            ValueError: If the provided accounts are not of the correct type.
        """
        if accounts_receivable.account_type != AccountType.ASSET:
            raise ValueError("accounts_receivable account must be of type Asset.")
        if sales_revenue.account_type != AccountType.REVENUE:
            raise ValueError("sales_revenue account must be of type Revenue.")
            
        self.general_journal = general_journal
        self.accounts_receivable = accounts_receivable
        self.sales_revenue = sales_revenue

    def record_sale(self, amount: float):
        """
        Records a single credit sale.
        
        This creates a standard transaction and posts it to the GeneralJournal.
        
        Args:
            amount: The amount of the sale.
        """
        if amount <= 0:
            raise ValueError("Sale amount must be positive.")
            
        sale_transaction = TransactionSymbol(
            debit=self.accounts_receivable,
            credit=self.sales_revenue,
            amount=amount
        )
        self.general_journal.record_entry(sale_transaction) 