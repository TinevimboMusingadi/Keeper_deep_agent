"""Test LangGraph API endpoints directly to verify authentication requirements."""
import requests
import json

# Configuration
DEPLOYMENT_URL = "http://127.0.0.1:2024"
ASSISTANT_ID = "finance"

print("Testing LangGraph API Endpoints")
print("=" * 60)

# Test 1: Check if server is running
print("\n1. Testing server health...")
try:
    response = requests.get(f"{DEPLOYMENT_URL}/docs", timeout=5)
    print(f"   ✓ Server is running (Status: {response.status_code})")
except Exception as e:
    print(f"   ✗ Server not accessible: {e}")
    exit(1)

# Test 2: List assistants (no auth)
print("\n2. Testing /assistants endpoint (no auth headers)...")
try:
    response = requests.get(
        f"{DEPLOYMENT_URL}/assistants",
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Success! Found {len(data.get('items', []))} assistants")
        if data.get('items'):
            print(f"   First assistant: {data['items'][0].get('assistant_id', 'N/A')}")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Search for finance assistant
print("\n3. Testing assistant search...")
try:
    response = requests.post(
        f"{DEPLOYMENT_URL}/assistants/search",
        headers={"Content-Type": "application/json"},
        json={"graph_id": ASSISTANT_ID, "limit": 10},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Success! Found {len(data.get('items', []))} assistants")
        if data.get('items'):
            assistant = data['items'][0]
            print(f"   Assistant ID: {assistant.get('assistant_id')}")
            print(f"   Graph ID: {assistant.get('graph_id')}")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Create a thread (no auth)
print("\n4. Testing thread creation...")
try:
    response = requests.post(
        f"{DEPLOYMENT_URL}/threads",
        headers={"Content-Type": "application/json"},
        json={},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        thread_id = data.get('thread_id')
        print(f"   ✓ Success! Created thread: {thread_id}")
        
        # Test 5: Submit a message to the thread
        print("\n5. Testing message submission...")
        try:
            submit_response = requests.post(
                f"{DEPLOYMENT_URL}/threads/{thread_id}/runs/stream",
                headers={
                    "Content-Type": "application/json",
                    # Explicitly NOT setting X-Api-Key or Authorization
                },
                json={
                    "assistant_id": ASSISTANT_ID,
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": "Hello, can you help me with finance tasks?"
                            }
                        ]
                    }
                },
                stream=True,
                timeout=10
            )
            print(f"   Status: {submit_response.status_code}")
            if submit_response.status_code == 200:
                print(f"   ✓ Success! Stream started")
                # Read first few chunks
                chunk_count = 0
                for line in submit_response.iter_lines():
                    if line:
                        chunk_count += 1
                        if chunk_count <= 3:
                            print(f"   Chunk {chunk_count}: {line.decode()[:100]}")
                        if chunk_count >= 3:
                            break
            else:
                print(f"   Response: {submit_response.text[:500]}")
        except Exception as e:
            print(f"   ✗ Error submitting message: {e}")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 6: Check API docs for auth requirements
print("\n6. Checking API documentation...")
try:
    response = requests.get(f"{DEPLOYMENT_URL}/openapi.json", timeout=5)
    if response.status_code == 200:
        openapi = response.json()
        # Check for security requirements
        if 'components' in openapi and 'securitySchemes' in openapi['components']:
            print(f"   Security schemes defined: {list(openapi['components']['securitySchemes'].keys())}")
        else:
            print(f"   ✓ No security schemes required (good for local dev)")
except Exception as e:
    print(f"   Note: Could not check OpenAPI spec: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("\nIf all tests pass, the API works without authentication.")
print("If tests fail with auth errors, we need to configure the SDK differently.")

