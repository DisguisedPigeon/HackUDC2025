import requests

# Credenciales OAuth2
client_id = "oauth-mkpsbox-oauthxdnrltwvvzqdrjkdimsnbxpro"
client_secret = "oI2F24R3uyAZMs_p"

# URL del token en el entorno sandbox
token_url = "https://auth.inditex.com:443/openam/oauth2/itxid/itxidmp/sandbox/access_token"

# Parámetros de la solicitud
data = {
    "grant_type": "client_credentials",
    "scope": "technology.catalog.read"
}

# Enviar la solicitud con autenticación básica
response = requests.post(token_url, data=data, auth=(client_id, client_secret))

# Ver resultado
if response.status_code == 200:
    token_info = response.json()
    print("Token obtenido:", token_info["access_token"])
else:
    print("Error:", response.status_code, response.text)

