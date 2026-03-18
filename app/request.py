"""import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Register a new user
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "company": "Test Co",
    "password": "securepassword123"
}
response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print("Register:", response.json())

# 2. Login (get access/refresh tokens)
login_data = {
    "username": "testuser",
    "password": "securepassword123"
}
response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]
print("Login:", tokens)

# Headers for authenticated requests
headers = {"Authorization": f"Bearer {access_token}"}

# 3. Create a conversation
response = requests.post(f"{BASE_URL}/rag/conversations", headers=headers)
conv_id = response.json()["conversation_id"]
print("Conversation ID:", conv_id)

# 4. Send a message (with optional files, web search)
# Example: Text-only message
files = []  # Or: [('files', open('doc.pdf', 'rb'))] for uploads
data = {
    "model": "llama-3.1-8b-instant",
    "enable_web_search": True,
    "message": "What is the capital of France?"
}
response = requests.post(
    f"{BASE_URL}/rag/conversations/{conv_id}/messages",
    headers=headers,
    data=data,
    files=files if files else None,
    stream=True
)
for chunk in response.iter_content(chunk_size=1024):
    if chunk:
        print(chunk.decode(), end='', flush=True)  # Streaming output

# 5. Get conversation history
response = requests.get(f"{BASE_URL}/rag/conversations/{conv_id}", headers=headers)
print("History:", response.json())

# 6. Refresh token
refresh_data = {"refresh_token": refresh_token}
response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
new_tokens = response.json()
print("New Tokens:", new_tokens)

# 7. Logout
logout_data = {"refresh_token": refresh_token}
response = requests.post(f"{BASE_URL}/auth/logout", json=logout_data)
print("Logout:", response.json())"""
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Login (get access/refresh tokens) - Change credentials if needed
login_data = {
    "username": "testuser",        # Update if your username is different
    "password": "securepassword123"  # Update with your actual password
}
response = requests.post(f"{BASE_URL}/auth/login", data=login_data)

if response.status_code != 200:
    print("Login Failed:", response.status_code, response.text)
else:
    tokens = response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    print("Login Success:", tokens)

    # Headers for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Create a conversation
    response = requests.post(f"{BASE_URL}/rag/conversations", headers=headers)
    if response.status_code == 201:
        conv_id = response.json()["conversation_id"]
        print("Conversation Created - ID:", conv_id)
    else:
        print("Failed to create conversation:", response.status_code, response.text)
        conv_id = None

    if conv_id:
        # 3. Send a message (text-only example)
        data = {
            "model": "llama-3.1-8b-instant",   # Change model if desired (from ALLOWED_MODELS)
            "enable_web_search": "true",       # "true" or "false" as string for form data
            "message": "What is the capital of France?"
        }
        # Optional: Add files for document RAG
        # files = [('files', open('your_document.pdf', 'rb'))]

        response = requests.post(
            f"{BASE_URL}/rag/conversations/{conv_id}/messages",
            headers=headers,
            data=data,
            # files=files if 'files' in locals() else None,
            stream=True
        )

        print("\n--- Assistant Response ---")
        if response.status_code == 200:
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    print(chunk, end='', flush=True)
            print("\n--- End of Response ---")
        else:
            print("Message Send Failed:", response.status_code)
            print("Response:", response.text)

        # 4. Get conversation history
        response = requests.get(f"{BASE_URL}/rag/conversations/{conv_id}", headers=headers)
        print("\nConversation History:", json.dumps(response.json(), indent=2))

    # 5. Refresh token (optional)
    refresh_data = {"refresh_token": refresh_token}
    response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
    print("Token Refresh:", response.json() if response.status_code == 200 else response.text)

    # 6. Logout (optional)
    logout_data = {"refresh_token": refresh_token}
    response = requests.post(f"{BASE_URL}/auth/logout", json=logout_data)
    print("Logout:", response.json())