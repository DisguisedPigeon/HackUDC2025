# Picture Motion Enhanced Clothing

Submission for HackUDC 2025 for the Inditex proposal

## Descripción del reto
El objetivo es crear una aplicación web o móvil que integre la [API de Visual Search de Inditex](https://developer.inditex.com/apimktplc/web/products/pubapimkt/protocols/REST/apis/visual-search/overview) para facilitar la búsqueda de productos similares a una imagen proporcionada por la persona usuaria. La aplicación debe ser intuitiva, rápida y ofrecer resultados precisos al explorar el catálogo de productos.

## Características principales
* **Carga de imágenes**: Permitir subir imágenes desde su dispositivo o capturarlas directamente con la cámara.
* **Búsqueda visual**: Utilizar la API de Visual Search para analizar la imagen y encontrar productos similares en el catálogo de Inditex.
* **Detalles del producto**: Mostrar información detallada de cada producto, incluyendo imágenes, descripciones, precios y disponibilidad.
* **Lista de deseos**: Permitir a los usuarios guardar productos favoritos para futuras referencias.
* **Compartir en redes sociales**: Facilitar la opción de compartir productos o listas de deseos en plataformas sociales.

## Requisitos técnicos
* Integración con la API de Visual Search de Inditex.
* Selección de un framework adecuado para aplicaciones web o móviles (por ejemplo, React, Angular, Flutter).
* Diseño responsive y centrado en la experiencia del usuario.
* Código bien documentado y bajo licencia open source en un repositorio público de GitHub.

## Criterios de evaluación
* Precisión y relevancia de los resultados de la búsqueda.
* Facilidad de uso y experiencia del usuario
* Innovación en las funcionalidades y diseño de la aplicación.
* Calidad y claridad del código fuente.

## TODO
- [ ] Visualizacion de prendas en WebGL

## VirtualEnv

Creamos el entorno virtual de python:

```bash
python -m venv venv
```

Activamos el entorno virtual (Linux/macOS):

```bash
source venv/bin/activate
```

Instalamos las dependencias:

```bash
pip install -r requirements.txt
```

Para desactivarlo:
```bash
deactivate
```

#### Nota

Para actualizar los requirements.txt

```bash
pip freeze > requirements.txt
```
