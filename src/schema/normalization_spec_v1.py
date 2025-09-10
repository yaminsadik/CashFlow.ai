# src/schema/normalization_spec_v1.py
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field

SPEC_VERSION = "normalization_spec_v1"

class AmountLogic(BaseModel):
    mode: Literal["signed_amount","debit_credit","type_flag"] = "signed_amount"
    amount_col: Optional[str] = None
    debit_col: Optional[str] = None
    credit_col: Optional[str] = None
    type_col: Optional[str] = None
    credit_tokens: List[str] = []
    debit_tokens: List[str] = []

class DateRules(BaseModel):
    known_formats: List[str] = []
    normalize_to: str = "YYYY-MM-DD"
    timezone: Optional[str] = None

class ClassifyRule(BaseModel):
    when: str
    set_category: str

class NormalizationSpec(BaseModel):
    column_mapping: Dict[str, Literal[
        "date","description","amount","debit","credit","balance","category","type","source"
    ]] = Field(default_factory=dict)
    amount_logic: AmountLogic = AmountLogic()
    date_rules: DateRules = DateRules()
    classify_rules: List[ClassifyRule] = Field(default_factory=list)
    drop_columns: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    confidence: float = 0.0
