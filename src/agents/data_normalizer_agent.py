# agents/data_normalizer_agent.py
from langchain_core.messages import SystemMessage, HumanMessage
from core.llm_prompts import SPEC_SYSTEM, SPEC_USER_TMPL
from schema.normalization_spec_v1 import NormalizationSpec
from core.models import get_model

def _sample(df, n=40):
    h = df.head(n//2); t = df.tail(n - len(h))
    return (h._append(t) if hasattr(h, "_append") else h.append(t)).fillna("").astype(str).to_dict("records")

async def infer_spec(raw_df):
    model = get_model()  # must support structured output / json schema
    headers = list(raw_df.columns)
    sample_rows = _sample(raw_df, 40)
    msgs = [
        SystemMessage(content=SPEC_SYSTEM),
        HumanMessage(content=SPEC_USER_TMPL.format(headers=headers, sample_rows=sample_rows)),
    ]
    spec: NormalizationSpec = await model.with_structured_output(NormalizationSpec).ainvoke(msgs)
    return spec
