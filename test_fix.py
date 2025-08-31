import requests

# Test the credit purchase endpoint
url = "http://localhost:8000/pay-per-use/credits/purchase"
data = {
    "email": "edgarjesusa@gmail.com",
    "package_id": "professional"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")