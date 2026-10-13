import requests

# Create a session so login "sticks" (like staying logged in)
session = requests.Session()

# Step 1: Log in
login_response = session.post(
    "http://127.0.0.1:5000/api/login",
    json={"username": "admin", "password": "admin123"}
)
print("Login result:", login_response.json())

# Step 2: Update slot A3 to occupied
update_response = session.post(
    "http://127.0.0.1:5000/api/slots/A3/update",
    json={"status": "occupied"}
)
print("Update result:", update_response.json())