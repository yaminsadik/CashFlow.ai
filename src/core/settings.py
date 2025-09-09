# core/settings.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL = "gpt-4o-mini"  # Cost-effective for prototyping

settings = Settings()

# Model factory function
from langchain_openai import ChatOpenAI

def get_model(model_name: str = None):
    return ChatOpenAI(
        model=model_name or settings.DEFAULT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0  # Deterministic for financial data
    )
