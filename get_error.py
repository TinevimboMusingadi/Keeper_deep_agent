import requests
import json

threads = requests.post('http://127.0.0.1:2024/threads/search', json={'limit': 1}).json()
t = threads[0]
thread_id = t["thread_id"]
state = requests.get(f'http://127.0.0.1:2024/threads/{thread_id}/state').json()

print(f"Thread: {thread_id}")
print(f"Status: {t.get('status')}")

if 'tasks' in state:
    for task in state['tasks']:
        print(f"\nTask: {task.get('name')}")
        print(f"Error: {task.get('error')}")

