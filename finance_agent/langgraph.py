"""
LangGraph entrypoint for finance agent.

Usage:
  langgraph dev
with langgraph.json pointing to this module's `agent`.
"""

from finance_agent.agent import create_finance_agent

agent = create_finance_agent()

__all__ = ["agent"]


