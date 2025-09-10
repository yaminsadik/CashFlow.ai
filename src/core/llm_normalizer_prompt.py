# core/llm_prompts.py
SPEC_SYSTEM = """You are a financial data normalizer.
Return ONLY JSON matching the NormalizationSpec schema.
Infer rules from headers + sample rows. Do NOT return the normalized rows."""

SPEC_USER_TMPL = """Target fields: date, description, amount, debit, credit, balance, category, type, source.
Rules:
1) amount positive for inflows, negative for outflows.
2) If both debit/credit exist: amount = credit - debit.
3) Normalize dates to YYYY-MM-DD.
Headers: {headers}
Sample rows (JSON, up to 50): {sample_rows}"""
