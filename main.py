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

app = FastAPI()

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
ID_TOKEN = os.getenv("ID_TOKEN")
UPLOAD_DIR = "uploads"
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")  # Usa el dominio del .env o localhost por defecto

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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

@app.post("/text-search")
async def text_search(search_request: TextSearchRequest):
    headers = {
        "Authorization": f"Bearer {ID_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "query": search_request.query,
        "page": search_request.page,
        "perPage": search_request.per_page
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(INDITEX_SEARCH_API_URL, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Inditex Search API")

@app.post("/visual-search")
async def visual_search(search_request: VisualSearchRequest):
    headers = {
        "Authorization": f"Bearer {ID_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "image": str(search_request.image_url),
        "page": search_request.page,
        "perPage": search_request.per_page
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(INDITEX_VISUAL_SEARCH_API_URL, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Inditex Visual Search API")

@app.post("/upload-and-search")
async def upload_and_search(file: UploadFile = File(...)):
    # Guardar el archivo
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Generar URL pública con protocolo https://
    public_url = f"https://{DOMAIN}/uploads/{unique_filename}"
    print(f"URL generada: {public_url}")  # Para debugging
    
    # Realizar la búsqueda visual
    headers = {
        "Authorization": f"Bearer {ID_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "image": public_url,
        "page": 1,
        "perPage": 10
    }

    try:
        # Realizar la búsqueda visual
        async with httpx.AsyncClient() as client:
            response = await client.get(INDITEX_VISUAL_SEARCH_API_URL, params=params, headers=headers)
        
        print(f"Respuesta de la API: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        
        # Procesar la respuesta de la API
        if response.status_code == 200:
            api_response = response.json()
        else:
            api_response = {"error": f"Failed to fetch data from Inditex Visual Search API: {response.text}"}
        
        # Eliminar el archivo después de recibir la respuesta de la API
        os.remove(file_path)
        print(f"Imagen eliminada: {file_path}")
        
        return api_response
    except Exception as e:
        # Si ocurre un error, asegúrate de eliminar el archivo de todos modos
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Imagen eliminada después de un error: {file_path}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

