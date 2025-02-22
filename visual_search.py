import os
import requests
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

# Parámetros de la solicitud
request_url = "https://api-sandbox.inditex.com/pubvsearch-sandbox/products"
key = os.getenv("ID_TOKEN")

image = "https://www.markamania.es/1127148-large_default/camiseta-blanca-stanleystella-rocker.jpg"

params = {
    "image": image,
    "page": 1,
    "perPage": 5
}

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

print("h:", headers) 

# Enviar la solicitud con autenticación básica
response = requests.get(request_url, params=params, headers=headers)

# Ver resultado
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