from fastapi import FastAPI, HTTPException, Request, File, UploadFile
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

app = FastAPI()

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

# Configurar templates
templates = Jinja2Templates(directory="templates")

load_dotenv()

INDITEX_SEARCH_API_URL = "https://api-sandbox.inditex.com/searchpmpa-sandbox/products"
INDITEX_VISUAL_SEARCH_API_URL = "https://api-sandbox.inditex.com/pubvsearch-sandbox/products"
UPLOAD_DIR = "uploads"
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")

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

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("hello.html", {"request": request})

@app.get("/text-search")
async def text_search(query: str, page: int = 1, per_page: int = 5):
    headers = {
        "Authorization": f"Bearer {os.getenv('ID_TOKEN')}",
        "Content-Type": "application/json"
    }
    params = {
        "query": query,
        "page": page,
        "perPage": per_page
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(INDITEX_SEARCH_API_URL, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Inditex Search API")

@app.get("/visual-search")
async def visual_search(image_url: HttpUrl, page: int = 1, per_page: int = 5):
    headers = {
        "Authorization": f"Bearer {os.getenv('ID_TOKEN')}",
        "Content-Type": "application/json"
    }
    params = {
        "image": str(image_url),
        "page": page,
        "perPage": per_page
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(INDITEX_VISUAL_SEARCH_API_URL, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Inditex Visual Search API")

@app.post("/upload-and-search")
async def upload_and_search(file: UploadFile = File(...)):
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Corregir la generación de la URL pública
    if DOMAIN.startswith(('http://', 'https://')):
        public_url = f"{DOMAIN}/uploads/{unique_filename}"
    else:
        public_url = f"https://{DOMAIN}/uploads/{unique_filename}"
    
    print(f"URL generada: {public_url}")
    
    headers = {
        "Authorization": f"Bearer {os.getenv('ID_TOKEN')}",
        "Content-Type": "application/json"
    }
    params = {
        "image": public_url,
        "page": 1,
        "perPage": 5
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(INDITEX_VISUAL_SEARCH_API_URL, params=params, headers=headers)
        
        print(f"Respuesta de la API: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        
        if response.status_code == 200:
            api_response = response.json()
        else:
            api_response = {"error": f"Failed to fetch data from Inditex Visual Search API: {response.text}"}
        
        os.remove(file_path)
        print(f"Imagen eliminada: {file_path}")
        
        return api_response
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Imagen eliminada después de un error: {file_path}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

