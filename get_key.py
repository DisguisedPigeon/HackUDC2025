import os
import requests
from dotenv import load_dotenv, set_key
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime, timedelta

load_dotenv()

client_id = os.getenv("OAUTH2_CLIENT")
client_secret = os.getenv("OAUTH2_SECRET")
token_url = "https://auth.inditex.com:443/openam/oauth2/itxid/itxidmp/access_token"
scope = "technology.catalog.read"

print(f"TOKEN_URL: {token_url}")

scheduler = BackgroundScheduler()

def truncate_token(token):
    return token[:10] + "..."

def get_token():
    data = {"grant_type": "client_credentials", "scope": scope}

    headers = {
        "User-Agent": "HackUDC2025/1.0",
    }

    response = requests.post(
        token_url, data=data, auth=(client_id, client_secret), headers=headers
    )

    if response.status_code == 200:
        token_info = response.json()
        set_key(".env", "ID_TOKEN", token_info["id_token"])

        truncated_token = truncate_token(token_info["id_token"])
        print(f"Token obtenido: {truncated_token}")
        
        expires_in_seconds = token_info["expires_in"]
        expiration_time = datetime.now() + timedelta(seconds=expires_in_seconds)
        print(f"El token expira en: {expires_in_seconds} segundos (a las {expiration_time.strftime('%Y-%m-%d %H:%M:%S')})")

        next_refresh = datetime.now() + timedelta(seconds=expires_in_seconds - 300)  # 5 minutos antes de que expire
        scheduler.add_job(get_token, "date", run_date=next_refresh)
        print(f"Próxima actualización programada para: {next_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"Error: {response.status_code} {response.text}")

def start_token_refresh():
    scheduler.start()
    get_token()

if __name__ == "__main__":
    start_token_refresh()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Proceso de actualización de token detenido")
        scheduler.shutdown()


