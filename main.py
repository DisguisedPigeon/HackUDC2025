from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl
import httpx
from dotenv import load_dotenv
import os
import shutil
from uuid import uuid4
from get_key import start_token_refresh
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

print("Iniciando la aplicación...")
logger.info("Iniciando la aplicación...")

# Iniciar el mecanismo de recarga de token
start_token_refresh()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configurar templates
templates = Jinja2Templates(directory="templates")

load_dotenv()

INDITEX_SEARCH_API_URL = "https://api.inditex.com/searchpmpa/products"
INDITEX_VISUAL_SEARCH_API_URL = "https://api.inditex.com/pubvsearch/products"
UPLOAD_DIR = "uploads"
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")

GLOBAL_HEADERS = {
    "Authorization": f"Bearer {os.getenv('ID_TOKEN')}",
    "Content-Type": "application/json",
    "User-Agent": "HackUDC2025/1.0"
}

print(f"INDITEX_SEARCH_API_URL: {INDITEX_SEARCH_API_URL}")
print(f"INDITEX_VISUAL_SEARCH_API_URL: {INDITEX_VISUAL_SEARCH_API_URL}")
print(f"DOMAIN: {DOMAIN}")
logger.info(f"INDITEX_SEARCH_API_URL: {INDITEX_SEARCH_API_URL}")
logger.info(f"INDITEX_VISUAL_SEARCH_API_URL: {INDITEX_VISUAL_SEARCH_API_URL}")
logger.info(f"DOMAIN: {DOMAIN}")

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_DIR, exist_ok=True)

class TextSearchRequest(BaseModel):
    query: str
    page: int = 1
    per_page: int = 5

class VisualSearchRequest(BaseModel):
    image_url: HttpUrl
    page: int = 1
    per_page: int = 5

@app.route("/")
async def visual_search_front(request: Request) -> Response:
    return templates.TemplateResponse(request=request, name="visual.html", context={})

@app.route("/results")
async def results_front(request: Request, page: int = 0) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
	    "other": True,
            "page": page,
            "results_1": [
                {"title": "Ligma", "description": "hallo"},
                {"title": "Big", "description": "hallo"},
                {"title": "Ballz", "description": "hallo"},
            ],
            "results_2": [
                {"title": "Sugon", "description": "hallo"},
                {"title": "Deez", "description": "hallo"},
                {"title": "Nutz", "description": "hallo"},
            ],
        },
    )


@app.route("/text")
async def text_search_front(request: Request) -> Response:
    return templates.TemplateResponse(request=request, name="text.html", context={})

@app.get("/text-search")
async def text_search(query: str, page: int = 1, per_page: int = 5):
    print(f"Iniciando búsqueda de texto con query: {query}, page: {page}, per_page: {per_page}")
    logger.info(f"Iniciando búsqueda de texto con query: {query}, page: {page}, per_page: {per_page}")
    
    params = {
        "query": query,
        "page": page,
        "perPage": per_page
    }

    print(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    print(f"Parámetros de la solicitud: {params}")
    logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    logger.info(f"Parámetros de la solicitud: {params}")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            INDITEX_SEARCH_API_URL, params=params, headers=GLOBAL_HEADERS
        )
    
    print(f"Código de respuesta de la API: {response.status_code}")
    logger.info(f"Código de respuesta de la API: {response.status_code}")
    
    if response.status_code == 200:
        print("Búsqueda de texto exitosa")
        logger.info("Búsqueda de texto exitosa")
        return response.json()
    else:
        print(f"Error en la búsqueda de texto: {response.text}")
        logger.error(f"Error en la búsqueda de texto: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch data from Inditex Search API: {response.text}")

@app.get("/visual-search")
async def visual_search(image_url: HttpUrl, page: int = 1, per_page: int = 5):
    print(f"Iniciando búsqueda visual con image_url: {image_url}, page: {page}, per_page: {per_page}")
    logger.info(f"Iniciando búsqueda visual con image_url: {image_url}, page: {page}, per_page: {per_page}")
    
    params = {
        "image": str(image_url),
        "page": page,
        "perPage": per_page
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
        return response.json()
    else:
        print(f"Error en la búsqueda visual: {response.text}")
        logger.error(f"Error en la búsqueda visual: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch data from Inditex Visual Search API: {response.text}")

@app.post("/upload-and-search")
async def upload_and_search(file: UploadFile = File(...)):
    print(f"Iniciando carga y búsqueda con archivo: {file.filename}")
    logger.info(f"Iniciando carga y búsqueda con archivo: {file.filename}")
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    if DOMAIN.startswith(('http://', 'https://')):
        public_url = f"{DOMAIN}/uploads/{unique_filename}"
    else:
        public_url = f"https://{DOMAIN}/uploads/{unique_filename}"
    
    print(f"URL generada: {public_url}")
    logger.info(f"URL generada: {public_url}")
    
    params = {
        "image": public_url,
        "page": 1,
        "perPage": 5
    }

    print(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    print(f"Parámetros de la solicitud: {params}")
    logger.info(f"Headers de la solicitud: {GLOBAL_HEADERS}")
    logger.info(f"Parámetros de la solicitud: {params}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                INDITEX_VISUAL_SEARCH_API_URL, params=params, headers=GLOBAL_HEADERS
            )
        
        print(f"Respuesta de la API: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        logger.info(f"Respuesta de la API: {response.status_code}")
        logger.info(f"Contenido de la respuesta: {response.text}")
        
        if response.status_code == 200:
            api_response = response.json()
            print("Búsqueda visual exitosa")
            logger.info("Búsqueda visual exitosa")
        else:
            api_response = {"error": f"Failed to fetch data from Inditex Visual Search API: {response.text}"}
            print(f"Error en la búsqueda visual: {response.text}")
            logger.error(f"Error en la búsqueda visual: {response.text}")
        
        os.remove(file_path)
        print(f"Imagen eliminada: {file_path}")
        logger.info(f"Imagen eliminada: {file_path}")
        
        return api_response
    except Exception as e:
        print(f"Excepción ocurrida: {str(e)}")
        logger.exception(f"Excepción ocurrida: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Imagen eliminada después de un error: {file_path}")
            logger.info(f"Imagen eliminada después de un error: {file_path}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Iniciando el servidor...")
    logger.info("Iniciando el servidor...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

