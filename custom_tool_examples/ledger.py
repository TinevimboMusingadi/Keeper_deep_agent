import json
from typing import Dict, List, Optional
from .symbolic import AccountSymbol, AccountType

class ChartOfAccounts:
    """
    Manages the master list of all accounts for a business entity in a
    hierarchical structure.
    """
    def __init__(self):
        self._accounts_by_code: Dict[str, AccountSymbol] = {}
        self._accounts_by_name: Dict[str, AccountSymbol] = {}

    def add_account(self, code: str, name: str, account_type: AccountType, parent_code: Optional[str] = None):
        """
        Adds a new account to the chart, optionally linking it to a parent.
        
        Args:
            code: The unique code for the account (e.g., "1010").
            name: The unique name for the account (e.g., "Cash").
            account_type: The type of the account (Asset, Liability, etc.).
            parent_code: The code of the parent account, if any.
            
        Returns:
            The newly created AccountSymbol.
            
        Raises:
            ValueError: If the code or name is already in use, or if the parent account does not exist.
        """
        if code in self._accounts_by_code:
            raise ValueError(f"Account with code '{code}' already exists.")
        if name in self._accounts_by_name:
            raise ValueError(f"Account with name '{name}' already exists.")
            
        parent = None
        if parent_code:
            if parent_code not in self._accounts_by_code:
                raise ValueError(f"Parent account with code '{parent_code}' does not exist.")
            parent = self._accounts_by_code[parent_code]
        
        account = AccountSymbol(code=code, name=name, account_type=account_type, parent=parent)
        self._accounts_by_code[code] = account
        self._accounts_by_name[name] = account
        return account

    def get_account(self, identifier: str) -> AccountSymbol:
        """
        Retrieves an account by its unique code or its name.
        
        Args:
            identifier: The code or name of the account.
            
        Returns:
            The corresponding AccountSymbol.
            
        Raises:
            KeyError: If no account with the given identifier is found.
        """
        # First, try to find by code (which is the primary key)
        if identifier in self._accounts_by_code:
            return self._accounts_by_code[identifier]
        
        # If not found by code, search by name
        for account in self._accounts_by_name.values():
            if account.name == identifier:
                return account
                
        raise KeyError(f"Account with identifier '{identifier}' not found.")

    def get_children(self, parent_identifier: str) -> List[AccountSymbol]:
        """Returns a list of all direct children of a given parent account."""
        parent = self.get_account(parent_identifier)
        return [acc for acc in self._accounts_by_code.values() if acc.parent == parent]

    def __len__(self):
        return len(self._accounts_by_code)

    def __iter__(self):
        # Return accounts sorted by code for consistent ordering
        return iter(sorted(self._accounts_by_code.values(), key=lambda acc: acc.code))

    def save(self, filepath: str):
        """Saves the Chart of Accounts to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump([acc.to_dict() for acc in self], f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'ChartOfAccounts':
        """Loads a Chart of Accounts from a JSON file."""
        coa = cls()
        with open(filepath, 'r') as f:
            accounts_data = json.load(f)
        
        # Must load accounts in order, so parents are created before children
        # This is a simplification; a more robust solution might do multiple passes.
        accounts_data.sort(key=lambda x: x['code'])
        
        for acc_data in accounts_data:
            coa.add_account(
                code=acc_data['code'],
                name=acc_data['name'],
                account_type=AccountType(acc_data['account_type']),
                parent_code=acc_data.get('parent_code')
            )
        return coa 