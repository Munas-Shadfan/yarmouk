import requests
import json

def test_chat():
    url = "http://127.0.0.1:8000/api/chat"
    payload = {
        "query": "hello, are you connected to the database?",
        "thread_id": "test_session_123"
    }
    headers = {'Content-Type': 'application/json'}
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Streaming response:")
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data = json.loads(decoded_line[6:])
                        content = data.get('content', '')
                        print(content, end='', flush=True)
                        if content == '[DONE]':
                            break
            print("\nStream finished successfully.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_chat()
