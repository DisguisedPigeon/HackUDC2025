import os
import requests
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

# Credenciales OAuth2
client_id = os.getenv("OAUTH2_CLIENT")
client_secret = os.getenv("OAUTH2_SECRET")
token_url = os.getenv("TOKEN_URL")
scope = os.getenv("SCOPE")

print("TOKEN_URL:", token_url)

# Parámetros de la solicitud
data = {
    "grant_type": "client_credentials",
    "scope": scope
}

# Enviar la solicitud con autenticación básica
response = requests.post(token_url, data=data, auth=(client_id, client_secret))

# Ver resultado
if response.status_code == 200:
    token_info = response.json()
    print("Token obtenido:", token_info["access_token"])
else:
    print("Error:", response.status_code, response.text)
