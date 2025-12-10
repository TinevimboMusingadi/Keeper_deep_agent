"""Test model initialization in the same way as the agent."""
import os
from dotenv import load_dotenv
load_dotenv()

print(f"ANTHROPIC_API_KEY: {os.environ.get('ANTHROPIC_API_KEY', '')[:25]}...")

from langchain_anthropic import ChatAnthropic

# Try creating model exactly like the agent does
model = ChatAnthropic(
    model_name="claude-sonnet-4-5-20250929",
    max_tokens=20000,
)

print(f"Model created: {model}")
print(f"Model: {model.model}")

# Try invoking
print("\nTesting invoke...")
response = model.invoke("Say hello")
print(f"Response: {response.content[:100]}...")

