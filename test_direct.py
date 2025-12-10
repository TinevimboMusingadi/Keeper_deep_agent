"""Test the finance agent directly without server."""
import os
from dotenv import load_dotenv
load_dotenv()

print(f"API Key found: {os.environ.get('ANTHROPIC_API_KEY', '')[:20]}...")

from finance_agent.agent import create_finance_agent

print("Creating finance agent...")
agent = create_finance_agent(workspace_root="./test_workspace")
print("Agent created!")

print("\nSending test message...")
result = agent.invoke({
    "messages": [{"type": "human", "content": "Hello! What can you help me with?"}]
})

print("\nResult:")
if "messages" in result:
    for msg in result["messages"]:
        print(f"  {msg.type}: {str(msg.content)[:200]}...")
else:
    print(result)

