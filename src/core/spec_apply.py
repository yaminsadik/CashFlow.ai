# core/spec_apply.py
import re, pandas as pd
from dateutil import parser as dtp
from schema.normalization_spec_v1 import NormalizationSpec
from schema.cashflow_direct_v1 import CANONICAL_COLUMNS

def _parse_date(x, known_formats):
    s = str(x).strip()
    if not s:
        return None
    for fmt in known_formats or []:
        try:
            return pd.to_datetime(s, format=fmt).date().isoformat()
        except Exception:
            pass
    try:
        return pd.to_datetime(dtp.parse(s, fuzzy=True)).date().isoformat()
    except Exception:
        return None

def _to_num(x):
    y = re.sub(r"[^\d\.\-\(\)]", "", str(x).replace(",", ""))
    neg = y.startswith("(") and y.endswith(")")
    y = y.strip("()")
    try:
        v = float(y) if y not in ("", "None") else 0.0
    except Exception:
        v = 0.0
    return -abs(v) if neg else v

def apply_spec(df: pd.DataFrame, spec: NormalizationSpec):
    issues = []

    # 1) Rename columns per spec
    df = df.rename(columns={src: dst for src, dst in spec.column_mapping.items() if src in df.columns})

    # 1a) Deduplicate columns after rename (keep first occurrence)
    if df.columns.duplicated().any():
        dupes = df.columns[df.columns.duplicated()].tolist()
        issues.append(f"Duplicate columns after rename: {dupes} (kept first occurrence).")
        df = df.loc[:, ~df.columns.duplicated()]

    # 2) Ensure expected working columns exist
    for c in ["date", "description", "amount", "debit", "credit", "balance", "category", "type", "source"]:
        if c not in df.columns:
            df[c] = None

    # 3) Parse dates (measure quality BEFORE dropping)
    parsed_dates = df["date"].apply(lambda v: _parse_date(v, spec.date_rules.known_formats))
    date_null_ratio = parsed_dates.isna().mean()
    df["date"] = parsed_dates

    # 4) Build signed amount
    if spec.amount_logic.mode == "signed_amount" and spec.amount_logic.amount_col:
        col = spec.amount_logic.amount_col
        if col in df.columns:
            df["amount"] = df[col].apply(_to_num)
        else:
            issues.append(f"Amount column '{col}' not found for signed_amount mode; defaulting to existing 'amount'.")
            df["amount"] = df["amount"].apply(_to_num)
    elif (
        spec.amount_logic.mode == "debit_credit"
        and spec.amount_logic.debit_col
        and spec.amount_logic.credit_col
        and spec.amount_logic.debit_col in df.columns
        and spec.amount_logic.credit_col in df.columns
    ):
        dr = df[spec.amount_logic.debit_col].apply(_to_num)
        cr = df[spec.amount_logic.credit_col].apply(_to_num)
        df["amount"] = cr - dr
        both_populated = ((dr.fillna(0) != 0) & (cr.fillna(0) != 0)).sum()
        if both_populated:
            issues.append(f"{both_populated} rows have BOTH debit and credit populated; using amount = credit - debit.")
    elif spec.amount_logic.mode == "type_flag" and spec.amount_logic.type_col:
        # Prefer explicit amount_col if provided; else fall back to 'amount'
        base_col = spec.amount_logic.amount_col if spec.amount_logic.amount_col in df.columns else "amount"
        base = df.get(base_col, 0).apply(_to_num)
        tcol = spec.amount_logic.type_col
        credits = tuple(x.upper() for x in (spec.amount_logic.credit_tokens or []))
        debits  = tuple(x.upper() for x in (spec.amount_logic.debit_tokens or []))

        def sign(row):
            t = str(row.get(tcol, "")).upper()
            if any(tok in t for tok in credits):
                return abs(row["__base"])
            if any(tok in t for tok in debits):
                return -abs(row["__base"])
            return row["__base"]

        tmp = pd.DataFrame({"__base": base, tcol: df.get(tcol)})
        df["amount"] = tmp.apply(sign, axis=1)
    else:
        # Fallback: coerce whatever is in 'amount'
        df["amount"] = df["amount"].apply(_to_num)
        issues.append("Amount logic incomplete in spec; coerced 'amount' numerically as fallback.")

    # 5) Direction from sign
    df["direction"] = df["amount"].apply(lambda x: "inflow" if (x or 0) > 0 else ("outflow" if (x or 0) < 0 else None))

    # 6) Simple categorization via regex/keywords
    for rule in spec.classify_rules:
        try:
            mask = df["description"].astype(str).str.contains(rule.when, case=False, na=False, regex=True)
            df.loc[mask, "category"] = df.loc[mask, "category"].fillna(rule.set_category)
        except Exception:
            issues.append(f"Invalid classify rule regex: {rule.when!r}")

    # 7) Quality checks (measured before dropping)
    if date_null_ratio > 0.10:
        issues.append(f">10% unparsable dates (actual: {date_null_ratio:.1%}).")

    zero_amt_ratio = (pd.to_numeric(df["amount"], errors="coerce").fillna(0) == 0).mean()
    if zero_amt_ratio > 0.20:
        issues.append(f">20% zero/invalid amounts (actual: {zero_amt_ratio:.1%}).")

    # 8) Housekeeping: drop rows without parsed dates, sort, enforce canonical order & types
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # Ensure all canonical columns exist, then order them
    for c in CANONICAL_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[CANONICAL_COLUMNS]

    # Light dtype coercion for numeric fields
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "balance" in df.columns:
        df["balance"] = pd.to_numeric(df["balance"], errors="coerce")

    return df, issues
