"""Example runner for the finance agent."""

import asyncio

from finance_agent.agent import create_finance_agent


async def main():
    agent = create_finance_agent()
    # Example invocation; replace with real user message.
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Ingest sample invoice.pdf and draft a balance sheet."}]}
    )
    print(result["messages"][-1]["content"])


if __name__ == "__main__":
    asyncio.run(main())


