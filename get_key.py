import os
import requests
from dotenv import load_dotenv, set_key

load_dotenv()

client_id = os.getenv("OAUTH2_CLIENT")
client_secret = os.getenv("OAUTH2_SECRET")
token_url = "https://auth.inditex.com:443/openam/oauth2/itxid/itxidmp/sandbox/access_token"
scope = "technology.catalog.read"

print("TOKEN_URL:", token_url)

data = {
    "grant_type": "client_credentials",
    "scope": scope
}

headers = {
    "User-Agent": "HackUDC2025/0.1",
}

# Request
response = requests.post(token_url, data=data, auth=(client_id, client_secret), headers=headers)

# See and save to .env
if response.status_code == 200:
    token_info = response.json()
    set_key(".env", "ID_TOKEN", token_info["id_token"])
    print("Token obtenido:", token_info["id_token"])
else:
    print("Error:", response.status_code, response.text)
