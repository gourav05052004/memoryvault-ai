import requests

# Login first
login_response = requests.post(
    "http://localhost:8001/auth/login",
    json={"email": "11f15.gouravkumarsonu@gmail.com", "password": "your_password"}
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    
    # Get memories
    headers = {"Authorization": f"Bearer {token}"}
    memories_response = requests.get("http://localhost:8001/memories", headers=headers)
    
    if memories_response.status_code == 200:
        memories = memories_response.json()
        print(f"Total memories: {len(memories)}\n")
        
        for i, mem in enumerate(memories[:2], 1):
            print(f"Memory {i}:")
            print(f"  Title: {mem.get('title')}")
            print(f"  Type: {mem.get('type')}")
            print(f"  Has fileUrl: {'fileUrl' in mem}")
            print(f"  fileUrl: {mem.get('fileUrl', 'NOT PRESENT')}")
            print(f"  fileName: {mem.get('fileName', 'NOT PRESENT')}")
            print()
    else:
        print(f"Failed to get memories: {memories_response.status_code}")
        print(memories_response.text)
else:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
