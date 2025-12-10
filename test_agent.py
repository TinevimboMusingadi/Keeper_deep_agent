"""Test script for the Finance Agent."""
import requests
import json
import base64

API_URL = "http://127.0.0.1:2024"

def test_agent():
    print("Testing Finance Agent...")
    
    # Create thread
    thread = requests.post(f"{API_URL}/threads", json={}).json()
    thread_id = thread["thread_id"]
    print(f"Created thread: {thread_id}")

    # Send test message
    body = {
        "assistant_id": "finance",
        "input": {
            "messages": [{"type": "human", "content": "Hello! What can you help me with?"}]
        }
    }
    print("Sending test message...")
    
    try:
        run = requests.post(f"{API_URL}/threads/{thread_id}/runs/wait", json=body, timeout=120).json()
        print("Test completed!")
        
        # Get state
        state = requests.get(f"{API_URL}/threads/{thread_id}/state").json()
        
        # Always check for error first
        if state.get("error"):
            error = state.get("error", "Unknown error")
            try:
                decoded = base64.b64decode(error).decode()
                err_obj = json.loads(decoded)
                print(f"\n❌ Error: {err_obj.get('error', 'Unknown')}")
                print(f"   Message: {err_obj.get('message', decoded)}")
            except:
                print(f"\n❌ Error: {error[:300]}")
        elif "values" in state and "messages" in state["values"]:
            msgs = state["values"]["messages"]
            if len(msgs) > 1:
                last_msg = msgs[-1]
                content = last_msg.get("content", "No content")
                print(f"\n✅ Agent Response:\n{content[:800]}...")
            else:
                print("Only one message (the input)")
                print(f"Full state: {json.dumps(state, indent=2)[:500]}")
        else:
            print(f"State: {json.dumps(state, indent=2)[:500]}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_agent()

