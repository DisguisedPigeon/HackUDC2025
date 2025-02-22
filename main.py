import logging
import colorlog

# Configurar el logger
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

from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Response, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, HttpUrl
import httpx
from dotenv import load_dotenv
import os
import shutil
from uuid import uuid4
from get_key import start_token_refresh
import json

app = FastAPI()

print("Iniciando la aplicación...")
logger.info("Iniciando la aplicación...")

# Iniciar el mecanismo de recarga de token
# start_token_refresh()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount(f"/{UPLOAD_DIR}", StaticFiles(directory=UPLOAD_DIR), name=UPLOAD_DIR)
# Configurar templates
templates = Jinja2Templates(directory="templates")

load_dotenv()

INDITEX_SEARCH_API_URL = "https://api.inditex.com/searchpmpa/products"
INDITEX_VISUAL_SEARCH_API_URL = "https://api.inditex.com/pubvsearch/products"
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")

GLOBAL_HEADERS = {
    "Authorization": f"Bearer {os.getenv('ID_TOKEN')}",
    "Content-Type": "application/json",
    "User-Agent": "HackUDC2025/1.0",
}

logger.info(f"INDITEX_SEARCH_API_URL: {INDITEX_SEARCH_API_URL}")
logger.info(f"INDITEX_VISUAL_SEARCH_API_URL: {INDITEX_VISUAL_SEARCH_API_URL}")
logger.info(f"DOMAIN: {DOMAIN}")


class TextSearchRequest(BaseModel):
    query: str
    page: int = 1
    per_page: int = 5


class VisualSearchRequest(BaseModel):
    image_url: HttpUrl
    page: int = 1
    per_page: int = 5

def generate_context(data):
    context = {}
    context["other"] = True
    context["page"] = 0 #page
    #TODO: complete symbol dict
    symbol = {
        "EUR": "€"
    }
    cont = 1
    cnt = 1
    limits = len(data)
    datas = []
    for item in data:
        oprice = item["price"]["value"]["original"]
        datas.append({
	"name": item["name"], 
	"price": "Price: " + str(item["price"]["value"]["current"]) + " " + symbol[item["price"]["currency"]],
	"oprice": "Original price: " + str(oprice) + " " + symbol[item["price"]["currency"]] if oprice == "" else "Original price: None",
	"link": "Link: " + item["link"],
	"brand": "Brand: " + item["brand"],
        })
        ++cnt
        # We collect data in batchs of 3 elements
        if cnt % 3 == 0:
            context["results_" + str(cont)] = datas
            ++cont
            datas=[]
    if cnt % 3 != 0:
        context["results_" + str(cont)] = datas
    return context

@app.route("/")
async def visual_search_front(request: Request) -> Response:
    return templates.TemplateResponse(request=request, name="visual.html", context={})

@app.post("/results")
async def results_front(request: Request, user_input: str = Form(...), page_number: str = Form(...), product_number: str = Form(...)) -> Response:
    print(f"Iniciando búsqueda visual con image_url: {user_input}, page: {page_number}, per_page: {product_number}")
    logger.info(f"Iniciando búsqueda visual con image_url: {user_input}, page: {page_number}, per_page: {product_number}")
    params = {
        "image": user_input,
        "page": page_number,
        "perPage": product_number
    }

    print(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    print(f"Parámetros de la solicitud: {params}")
    logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    logger.info(f"Parámetros de la solicitud: {params}")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            INDITEX_VISUAL_SEARCH_API_URL, params=params, headers=GLOBAL_HEADERS
        )
    
    print(f"Código de respuesta de la API: {response.status_code}")
    logger.info(f"Código de respuesta de la API: {response.status_code}")
    
        
    if response.status_code == 200:
        print("Búsqueda visual exitosa")
        logger.info("Búsqueda visual exitosa")
        data = response.json()
        context = generate_context(data)
                    
        return templates.TemplateResponse(
                request=request,
                name="results.html",
                context=context,
            )

    else:
        print(f"Error en la búsqueda visual: {response.text}")
        logger.error(f"Error en la búsqueda visual: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch data from Inditex Visual Search API: {response.text}")


@app.route("/text", methods=('GET', 'POST'))
async def text_search_front(request: Request) -> Response:
    if request.method == 'POST':
        return redirect(url_for('results'))
    return templates.TemplateResponse(request=request, name="text.html", context={})


@app.get("/text-search")
async def text_search(query: str, page: int = 1, per_page: int = 5):
    logger.info(
        f"Iniciando búsqueda de texto con query: {query}, page: {page}, per_page: {per_page}"
    )

    params = {"query": query, "page": page, "perPage": per_page}

    logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
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

    logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
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
async def upload_and_search(myFile: UploadFile = File(...), page_number: str = Form(...), product_number: str = Form(...)):
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
        "page": page_number,
        "perPage": product_number
    }

    logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
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
        logger.exception(f"Excepción ocurrida: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Imagen eliminada después de un error: {file_path}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class Clothes3dRepository:
    _idUrlTable: dict[int, str]

    @staticmethod
    def getUrlById(id: int) -> dict[str, str]:
        id = str(id)
        return (
            None
            if id not in Clothes3dRepository._idUrlTable
            else Clothes3dRepository._idUrlTable[id]
        )


with open("./idClothesMap.json") as io:
    Clothes3dRepository._idUrlTable = json.load(io)


class Clothes3dService:
    _repo: Clothes3dRepository = Clothes3dRepository()
    _defaultId = 0

    @staticmethod
    def getUrlById(id: int) -> dict[str, str]:
        url = Clothes3dService._repo.getUrlById(id)
        if not url:
            url = Clothes3dService._repo.getUrlById(Clothes3dService._defaultId)
        return url


@app.get("/clothes-3d")
async def clothes_3d(id: int):
    return Clothes3dService.getUrlById(id)


"""
@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}
"""
if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando el servidor...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
