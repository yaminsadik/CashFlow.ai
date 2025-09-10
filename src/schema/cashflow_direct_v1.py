# src/schema/cashflow_direct_v1.py
from typing import Optional, Literal
from pydantic import BaseModel

SCHEMA_VERSION = "cashflow_direct_v1"

CANONICAL_COLUMNS = ["date","description","amount","direction","category","balance","source"]
DTYPES = {"date":"string","description":"string","amount":"float",
          "direction":"string","category":"string","balance":"float","source":"string"}

Direction = Literal["inflow","outflow"]

class CashflowRow(BaseModel):
    date: str                      # YYYY-MM-DD
    description: str
    amount: float                  # + inflow, - outflow
    direction: Optional[Direction] = None
    category: Optional[str] = None
    balance: Optional[float] = None
    source: Optional[str] = None
