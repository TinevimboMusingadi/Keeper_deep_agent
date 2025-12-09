from typing import List, Tuple, Dict
from .ledger import ChartOfAccounts
from .engine import ComputationalEngine
from .symbolic import AccountType
import math

class FinancialReporter:
    """
    Generates standard financial reports from a computed ledger.
    """
    def __init__(self, engine: ComputationalEngine, coa: ChartOfAccounts):
        """
        Initializes the reporter.
        
        Args:
            engine: A ComputationalEngine instance *after* balances have been computed.
            coa: The ChartOfAccounts used by the engine.
        """
        self.engine = engine
        self.coa = coa
        self._net_income = None # Cache for net income

    def _get_balance_of_children(self, parent_identifier: str) -> float:
        """Recursively calculates the total balance of an account and all its children."""
        parent_account = self.coa.get_account(parent_identifier)
        total_balance = self.engine.get_balance(parent_account.name)
        
        child_accounts = self.coa.get_children(parent_identifier)
        for child in child_accounts:
            total_balance += self._get_balance_of_children(child.code)
            
        return total_balance

    def generate_trial_balance(self) -> List[Tuple[str, str, float, float]]:
        """
        Generates a formatted trial balance.
        
        The trial balance lists all accounts from the Chart of Accounts and their
        final debit or credit balances. It's used to verify that the total
        of all debit balances equals the total of all credit balances.
        
        Returns:
            A list of tuples, where each tuple represents a row:
            (Account Code, Account Name, Debit Balance, Credit Balance)
            For each row, either the debit or credit will be 0.
        """
        report_rows = []
        
        for account in self.coa:
            balance = self.engine.get_balance(account.name)
            
            # Skip accounts with no balance and no children (i.e., empty parents)
            if balance == 0 and not self.coa.get_children(account.code):
                continue

            debit_balance = balance if balance > 0 else 0.0
            credit_balance = abs(balance) if balance < 0 else 0.0
            
            report_rows.append((account.code, account.name, debit_balance, credit_balance))
            
        return report_rows 

    def generate_income_statement(self) -> Tuple[List[Dict], float]:
        """
        Generates a simple income statement.
        
        Returns:
            A tuple containing:
            - A list of dictionaries for each line item (revenue/expense).
            - The final Net Income.
        """
        report = []
        total_revenue = 0.0
        total_expense = 0.0

        for acc in self.coa:
            # We only care about top-level category accounts for the report
            if acc.parent:
                continue

            if acc.account_type == AccountType.REVENUE:
                balance = abs(self._get_balance_of_children(acc.code))
                total_revenue += balance
                report.append({"category": acc.name, "amount": balance})
            
            elif acc.account_type == AccountType.EXPENSE:
                balance = self._get_balance_of_children(acc.code)
                total_expense += balance
                report.append({"category": acc.name, "amount": -balance})

        net_income = total_revenue - total_expense
        self._net_income = net_income # Cache the result for the balance sheet
        return report, net_income

    def generate_balance_sheet(self) -> Tuple[Dict, bool]:
        """
        Generates a simple balance sheet.
        
        Returns:
            A tuple containing:
            - A dictionary with the totals for Assets, Liabilities, and Equity.
            - A boolean indicating if the balance sheet is balanced.
        """
        if self._net_income is None:
            # Ensure income statement is calculated first
            _, _ = self.generate_income_statement()

        totals = { "Assets": 0.0, "Liabilities": 0.0, "Equity": 0.0 }

        for acc in self.coa:
            if acc.parent:
                continue
            
            balance = self._get_balance_of_children(acc.code)
            if acc.account_type == AccountType.ASSET:
                totals["Assets"] += balance
            elif acc.account_type == AccountType.LIABILITY:
                totals["Liabilities"] += abs(balance)
            elif acc.account_type == AccountType.EQUITY:
                totals["Equity"] += abs(balance)
        
        # Add the current period's earnings to equity
        totals["Equity"] += self._net_income
        
        # Check if Assets = Liabilities + Equity
        is_balanced = math.isclose(totals["Assets"], totals["Liabilities"] + totals["Equity"])
        
        return totals, is_balanced

    def generate_financial_ratios(self) -> Dict[str, float]:
        """
        Calculates a dictionary of key financial ratios.
        
        Returns:
            A dictionary containing common ratios. Returns infinity if a
            denominator is zero.
        """
        if self._net_income is None:
            self.generate_income_statement()
            
        bs_totals, _ = self.generate_balance_sheet()
        
        # For simplicity, we assume 'Assets' are current assets and
        # 'Liabilities' are current liabilities. A more detailed CoA
        # would be needed for a more precise calculation.
        current_assets = bs_totals["Assets"]
        current_liabilities = bs_totals["Liabilities"]
        total_equity = bs_totals["Equity"]
        
        ratios = {}
        
        # Liquidity Ratio: Current Ratio
        if current_liabilities > 0:
            ratios["current_ratio"] = current_assets / current_liabilities
        else:
            ratios["current_ratio"] = float('inf') if current_assets > 0 else 0.0

        # Solvency Ratio: Debt-to-Equity Ratio
        if total_equity > 0:
            ratios["debt_to_equity_ratio"] = current_liabilities / total_equity
        else:
            ratios["debt_to_equity_ratio"] = float('inf') if current_liabilities > 0 else 0.0

        return ratios 