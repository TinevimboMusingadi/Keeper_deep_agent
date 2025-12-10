"""
LangGraph entrypoint for finance agent.

Usage:
  langgraph dev
with langgraph.json pointing to this module's `agent`.
"""
import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Debug: print API key status
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
print(f"[langgraph.py] ANTHROPIC_API_KEY loaded: {api_key[:20]}..." if api_key else "[langgraph.py] WARNING: No ANTHROPIC_API_KEY found!")

from finance_agent.agent import create_finance_agent

agent = create_finance_agent()

__all__ = ["agent"]


