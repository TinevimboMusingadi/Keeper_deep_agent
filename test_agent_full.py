"""Test the full finance agent with deepagents."""
import asyncio
from finance_agent.agent import create_finance_agent

async def test_agent():
    print("Creating Finance Agent...")
    agent = create_finance_agent()
    print("✓ Agent created successfully")
    
    print("\nTesting agent with a simple query...")
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Hello, can you help me with finance tasks?"
        }]
    })
    
    print("✓ Agent responded successfully")
    if result and "messages" in result:
        last_msg = result["messages"][-1]
        if hasattr(last_msg, "content"):
            print(f"\nAgent response: {last_msg.content[:200]}...")
        else:
            print(f"\nAgent response type: {type(last_msg)}")

if __name__ == "__main__":
    asyncio.run(test_agent())


