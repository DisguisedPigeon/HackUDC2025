import os
import requests
from dotenv import load_dotenv

load_dotenv()

request_url = "https://api.inditex.com/searchpmpa/products"
key = os.getenv("ID_TOKEN")

text = "shirt"

params = {"query": text, "page": 1, "perPage": 5}

headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "HackUDC/0.1"}

print("h:", headers)

# Send request
response = requests.get(request_url, params=params, headers=headers)

# See
if response.status_code == 200:
    data = response.json()
    # Print all fields and their values
    if isinstance(data, dict):  # If the response is a dictionary
        for key, value in data.items():
            print(f"{key}: {value}")
    elif isinstance(data, list):  # If the response is a list of dictionaries
        for index, item in enumerate(data):
            print(f"Item {index + 1}:")
            if isinstance(item, dict):
                for key, value in item.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {item}")
    else:
        print("Unexpected response format:", data)
else:
    print("Error:", response.status_code, response.text)
