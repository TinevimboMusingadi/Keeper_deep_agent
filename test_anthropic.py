"""Test Anthropic API key directly."""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ANTHROPIC_API_KEY not found in environment")
else:
    print(f"✅ Found API key: {api_key[:20]}...")
    
    # Test with langchain-anthropic
    try:
        from langchain_anthropic import ChatAnthropic
        
        model = ChatAnthropic(model_name="claude-sonnet-4-5-20250929", max_tokens=100)
        response = model.invoke("Say 'Hello, the API key works!'")
        print(f"✅ Response: {response.content}")
    except Exception as e:
        print(f"❌ Error: {e}")

