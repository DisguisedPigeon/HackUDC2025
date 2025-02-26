import hashlib
import json
import logging
import os
import re
import shutil
from datetime import datetime, timedelta
from uuid import uuid4

import colorlog
import httpx
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import get_key, load_dotenv, set_key
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

# Configure logger
handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s%(reset)s:     %(message)s",
        log_colors={
            "INFO": "green",
            "DEBUG": "white",
            "WARNING": "white",
            "ERROR": "white",
            "CRITICAL": "white",
        },
    )
)

logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

load_dotenv()

app = FastAPI()

logger.info("Iniciando la aplicación...")

# Token refresh configuration
client_id = os.getenv("OAUTH2_CLIENT")
client_secret = os.getenv("OAUTH2_SECRET")
token_url = "https://auth.inditex.com:443/openam/oauth2/itxid/itxidmp/access_token"
scope = "technology.catalog.read"

logger.info(f"TOKEN_URL: {token_url}")

scheduler = BackgroundScheduler()


def truncate_token(token):
    return token[:10] + "..."


GLOBAL_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "HackUDC2025/1.0",
}


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
        logger.info(f"Token obtenido: {truncated_token}")

        expires_in_seconds = token_info["expires_in"]
        expiration_time = datetime.now() + timedelta(seconds=expires_in_seconds)
        logger.info(
            f"El token expira en: {expires_in_seconds} segundos (a las {expiration_time.strftime('%Y-%m-%d %H:%M:%S')})"
        )

        next_refresh = datetime.now() + timedelta(
            seconds=expires_in_seconds - 300
        )  # 5 minutos antes de que expire
        scheduler.add_job(get_token, "date", run_date=next_refresh)
        logger.info(
            f"Próxima actualización programada para: {next_refresh.strftime('%Y-%m-%d %H:%M:%S')} (5 mins antes de su expiración)"
        )
        # The token is now globaly accesible
        GLOBAL_HEADERS["Authorization"] = f"Bearer {get_key('.env', 'ID_TOKEN')}"

    else:
        logger.error(f" {response.status_code} {response.text}")


def start_token_refresh():
    scheduler.start()
    get_token()


# Start token refresh mechanism
start_token_refresh()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(f"/{UPLOAD_DIR}", StaticFiles(directory=UPLOAD_DIR), name=UPLOAD_DIR)

# Configure templates
templates = Jinja2Templates(directory="templates")

INDITEX_SEARCH_API_URL = "https://api.inditex.com/searchpmpa/products"
INDITEX_VISUAL_SEARCH_API_URL = "https://api.inditex.com/pubvsearch/products"
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")


logger.info(f"INDITEX_SEARCH_API_URL: {INDITEX_SEARCH_API_URL}")
logger.info(f"INDITEX_VISUAL_SEARCH_API_URL: {INDITEX_VISUAL_SEARCH_API_URL}")
logger.info(f"DOMAIN: {DOMAIN}")


class TextSearchRequest(BaseModel):
    product: str
    brand: str
    page_number: int = 1
    product_number: int = 5


class VisualSearchRequest(BaseModel):
    image_url: HttpUrl
    page: int = 1
    per_page: int = 5


def generate_context(data):
    context = {}
    context["other"] = True
    context["page"] = 0
    symbol = {"EUR": "€"}
    datas = []
    for item in data:
        oprice = item["price"]["value"]["original"]
        datas.append(
            {
                "name": item["name"],
                "price": "Price: "
                + str(item["price"]["value"]["current"])
                + " "
                + symbol[item["price"]["currency"]],
                "oprice": "Original price: "
                + str(oprice)
                + " "
                + symbol[item["price"]["currency"]]
                if oprice
                else "Original price: None",
                "link": item["link"],
                "brand": "Brand: " + item["brand"],
            }
        )
    context["results"] = datas

    return context


@app.route("/")
async def visual_search_front(request: Request):
    return templates.TemplateResponse(request=request, name="visual.html", context={})


@app.post("/text-results")
async def results_front(
    request: Request,
    form_data: TextSearchRequest = Form(...)
):
    logger.info(
        f"Iniciando búsqueda visual con image_url: {form_data.product}, page: {form_data.page_number}, per_page: {form_data.product_number}"
    )
    if form_data.brand:
            params = {
                "query": form_data.product,
                "brand": form_data.brand,
                "page": form_data.page_number,
                "perPage": form_data.product_number,
            }
    else:
        params = {"query": form_data.product, "page": form_data.page_number, "perPage": form_data.product_number}

    # logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    logger.info(f"Parámetros de la solicitud: {params}")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            INDITEX_SEARCH_API_URL, params=params, headers=GLOBAL_HEADERS
        )

    logger.info(f"Código de respuesta de la API: {response.status_code}")

    if response.status_code == 200:
        logger.info("Búsqueda textual exitosa")
        data = response.json()
        context = generate_context(data)

        return templates.TemplateResponse(
            request=request,
            name="results.html",
            context=context,
        )
    else:
        logger.error(f"Error en la búsqueda visual: {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch data from Inditex Visual Search API: {response.text}",
        )


@app.route("/text", methods=("GET", "POST"))
async def text_search_front(request: Request):
    if request.method == "POST":
        return redirect(url_for("results"))
    return templates.TemplateResponse(request=request, name="text.html", context={})


@app.get("/text-search")
async def text_search(query: str, brand: str, page: int = 1, per_page: int = 5):
    logger.info(
        f"Iniciando búsqueda de texto con query: {query}, page: {page}, per_page: {per_page}"
    )

    params = {"query": query, "brand": brand, "page": page, "perPage": per_page}

    # logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    logger.info(f"Parámetros de la solicitud: {params}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                INDITEX_SEARCH_API_URL, params=params, headers=GLOBAL_HEADERS
            )

        logger.info(f"Código de respuesta de la API: {response.status_code}")

        if response.status_code == 200:
            logger.info("Búsqueda de texto exitosa")
            return response.json()
        else:
            logger.error(f"Error en la búsqueda de texto: {response.text}")
            error_message = (
                f"Failed to fetch data from Inditex Search API: {response.text}"
            )
            raise HTTPException(status_code=response.status_code, detail=error_message)
    except httpx.RequestError as exc:
        logger.error(f"Error de conexión en la búsqueda de texto: {exc}")
        raise HTTPException(status_code=500, detail=f"Connection error: {exc}")


@app.get("/visual-search")
async def visual_search(image_url: HttpUrl, page: int = 1, per_page: int = 5):
    logger.info(
        f"Iniciando búsqueda visual con image_url: {image_url}, page: {page}, per_page: {per_page}"
    )

    params = {"image": str(image_url), "page": page, "perPage": per_page}

    # logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    logger.info(f"Parámetros de la solicitud: {params}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                INDITEX_VISUAL_SEARCH_API_URL, params=params, headers=GLOBAL_HEADERS
            )

        logger.info(f"Código de respuesta de la API: {response.status_code}")

        if response.status_code == 200:
            logger.info("Búsqueda visual exitosa")
            return response.json()
        else:
            logger.error(f"Error en la búsqueda visual: {response.text}")
            error_message = (
                f"Failed to fetch data from Inditex Visual Search API: {response.text}"
            )
            raise HTTPException(status_code=response.status_code, detail=error_message)
    except httpx.RequestError as exc:
        logger.error(f"Error de conexión en la búsqueda visual: {exc}")
        raise HTTPException(status_code=500, detail=f"Connection error: {exc}")


@app.post("/upload-and-search")
async def upload_and_search(
    request: Request,
    myFile: UploadFile = File(...),
    page_number: str = Form(...),
    product_number: str = Form(...),
):
    logger.info(f"Iniciando carga y búsqueda con archivo: {myFile.filename}")

    file_extension = os.path.splitext(myFile.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(myFile.file, buffer)

    if DOMAIN.startswith(("http://", "https://")):
        public_url = f"{DOMAIN}/uploads/{unique_filename}"
    else:
        public_url = f"https://{DOMAIN}/uploads/{unique_filename}"

    logger.info(f"URL generada: {public_url}")

    params = {
        "image": public_url,
        "page": int(page_number),
        "perPage": int(product_number),
    }

    # logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    logger.info(f"Parámetros de la solicitud: {params}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                INDITEX_VISUAL_SEARCH_API_URL, params=params, headers=GLOBAL_HEADERS
            )

        logger.info(f"Respuesta de la API: {response.status_code}")
        logger.info(f"Contenido de la respuesta: {response.text}")

        if response.status_code == 200:
            api_response = response.json()
            logger.info("Búsqueda visual exitosa")
            data = response.json()
            context = generate_context(data)

            os.remove(file_path)
            logger.info(f"Imagen eliminada: {file_path}")

            return templates.TemplateResponse(
                request=request,
                name="results.html",
                context=context,
            )
        else:
            api_response = {
                "error": f"Failed to fetch data from Inditex Visual Search API: {response.text}"
            }
            logger.error(f"Error en la búsqueda visual: {response.text}")

        os.remove(file_path)
        logger.info(f"Imagen eliminada: {file_path}")

        return api_response
    except httpx.RequestError as exc:
        logger.error(f"Error de conexión en la carga y búsqueda: {exc}")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Imagen eliminada después de un error: {file_path}")
        raise HTTPException(status_code=500, detail=f"Connection error: {exc}")
    except Exception as e:
        logger.error(f"Excepción ocurrida: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Imagen eliminada después de un error: {file_path}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class Clothes3dRepository:
    _classIdUrlsTable: dict[str, list[str, str]]
    _nameClassIdTable: dict[str, int]

    @staticmethod
    def getUrlsByClassId(classId: int) -> list[dict[str, str]]:
        classId = str(classId)
        return (
            []
            if classId not in Clothes3dRepository._classIdUrlsTable
            else Clothes3dRepository._classIdUrlsTable[classId]
        )

    @staticmethod
    def getNameAllClass() -> list[int]:
        return Clothes3dRepository._nameClassIdTable.keys()

    @staticmethod
    def getNameClassId(name: str) -> int:
        return (
            None
            if name not in Clothes3dRepository._nameClassIdTable
            else Clothes3dRepository._nameClassIdTable[name]
        )


with open("./idClothesMap.json") as io:
    Clothes3dRepository._classIdUrlsTable = json.load(io)

with open("./nameClassId.json") as io:
    Clothes3dRepository._nameClassIdTable = json.load(io)


def extraer_palabra(cadena, lista_palabras):
    patron = r"\b(" + "|".join(map(re.escape, lista_palabras)) + r")\b"
    coincidencia = re.search(patron, cadena, re.IGNORECASE)
    return coincidencia.group(0) if coincidencia else None


class Clothes3dService:
    _repo: Clothes3dRepository = Clothes3dRepository()
    _defaultId = 0

    @staticmethod
    def getUrlByProductName(product_name: str) -> dict[str, str]:
        classes = Clothes3dService._repo.getNameAllClass()
        className = extraer_palabra(product_name, classes)
        classId = Clothes3dService._repo.getNameClassId(className)

        urls = Clothes3dService._repo.getUrlsByClassId(classId)
        h = hashlib.new("sha256")
        h.update(product_name.encode())
        print(h.hexdigest())
        return [] if not urls else urls[int.from_bytes(h.digest(), "big") % len(urls)]


@app.get("/clothes-3d")
async def clothes_3d(product_name: str):
    return Clothes3dService.getUrlByProductName(product_name)


app.mount("/", StaticFiles(directory="favicon"), name="favicon")
if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando el servidor...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
