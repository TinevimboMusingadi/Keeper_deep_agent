from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class AccountType(Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


@dataclass
class AccountSymbol:
    code: str
    name: str
    account_type: AccountType
    parent: Optional["AccountSymbol"] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "account_type": self.account_type.value,
            "parent_code": self.parent.code if self.parent else None,
        }


@dataclass
class TransactionSymbol:
    debit: AccountSymbol
    credit: AccountSymbol
    amount: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "debit_code": self.debit.code,
            "credit_code": self.credit.code,
            "amount": self.amount,
        }


