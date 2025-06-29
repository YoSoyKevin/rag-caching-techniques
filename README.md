# LangChain RAG API con FastAPI, PostgreSQL (pgvector) y Google Gemini

## Enfoque: Semantic Cache y Exact Cache

Este proyecto está enfocado en la implementación y demostración de dos técnicas clave para optimizar sistemas RAG (Retrieval-Augmented Generation):

### ¿Qué es Exact Cache?
- **Exact Cache** almacena y reutiliza respuestas para prompts que coinciden exactamente con consultas previas.
- Es ideal para reducir latencia y costo cuando los usuarios repiten preguntas idénticas.
- En este proyecto, el endpoint `/rag/query_exact` implementa esta técnica.

### ¿Qué es Semantic Cache?
- **Semantic Cache** almacena respuestas y las recupera cuando una nueva consulta es semánticamente similar (aunque no idéntica) a una consulta previa.
- Utiliza embeddings y búsqueda de similitud para encontrar coincidencias.
- El endpoint `/rag/query_semantic` implementa esta técnica.

### ¿Por qué son importantes?
- **Ahorro de costos:** Menos llamadas al LLM.
- **Reducción de latencia:** Respuestas inmediatas desde cache.
- **Mejor experiencia de usuario:** Respuestas coherentes y rápidas.
- **Escalabilidad:** Menor carga en el backend y el modelo.

---

## Ejemplo de uso

### Exact Cache
```bash
curl -X POST http://localhost:8000/rag/query_exact \
  -H "Content-Type: application/json" \
  -d '{"prompt": "¿Cuál es la capital de Francia?"}'
```

### Semantic Cache
```bash
curl -X POST http://localhost:8000/rag/query_semantic \
  -H "Content-Type: application/json" \
  -d '{"prompt": "¿Qué ciudad es la capital de Francia?"}'
```

---

Este proyecto es una base profesional para sistemas de Retrieval Augmented Generation (RAG) usando LangChain (>=0.2.x), FastAPI y PostgreSQL con la extensión pgvector. Incluye integración con Google Gemini para embeddings y LLM, y está listo para producción pequeña o media.

## Estructura de Carpetas

```
├── src
│   ├── app
│   │   ├── db           # Lógica de conexión y utilidades de base de datos
│   │   ├── schemas      # Modelos Pydantic (requests/responses)
│   │   ├── middleware   # Middlewares (logging, etc)
│   │   └── dependencies # Inyección de dependencias
│   ├── cache            # Lógica de cache (exacto y semántico)
│   ├── indexer          # Lógica de indexado y almacenamiento de embeddings
│   └── retriever        # Lógica de recuperación RAG
├── config               # Configuración y variables de entorno
├── db                   # Scripts SQL para la base de datos
├── docs                 # Documentación adicional (tipos de cache, etc)
├── tests                # Pruebas automáticas con pytest
├── README.md            # Documentación
├── requirements.txt     # Dependencias
├── Dockerfile           # Imagen de la app FastAPI
└── docker-compose.yml   # Orquestación de contenedores
```

## Características
- RAG con LangChain (LCEL)
- Embeddings y LLM: Google Gemini API
- Vector store: PostgreSQL + pgvector
- API REST para consulta y reindexado
- Logging y caché de prompts
- Pruebas automáticas con pytest
- Listo para producción pequeña/mediana

## Requisitos
- Python >= 3.10
- Docker y docker-compose
- Clave API de Google Gemini (variable de entorno `GOOGLE_API_KEY`)
- (Opcional) Umbral de cache semántico: `CACHE_DISTANCE_THRESHOLD` (por defecto: -0.95). Para similitud coseno, valores más cercanos a -1 son más similares. Ajusta este valor en tu `.env` para controlar la sensibilidad del semantic cache. Ahora solo se considera hit si la distancia del embedding más cercano está entre -1 y el threshold configurado.
- En los logs del semantic cache se muestra el porcentaje de similitud aproximado: -1.0 equivale a 100% similar, 0.0 a 50%, y 1.0 a 0%. El sistema considera hit si la distancia es menor o igual al threshold configurado (más negativa = más similar).

## Despliegue rápido

1. Copia tu clave de Google Gemini en `config/.env`:
   ```
   GOOGLE_API_KEY=tu_clave
<<<<<<< HEAD
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=postgres
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   EMBEDDING_MODEL=models/embedding-001  # Modelo de embeddings de Google Gemini
   LLM_MODEL=gemini-2.5-flash           # Modelo LLM de Google Gemini
   CACHE_DISTANCE_THRESHOLD=-0.95
=======
   POSTGRES_PASSWORD=postgres
   POSTGRES_USER=postgres
   POSTGRES_DB=RAG
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/RAG
   EMBEDDING_MODEL=models/embedding-001  # Modelo de embeddings de Google Gemini
   LLM_MODEL=gemini-2.5-flash           # Modelo LLM de Google Gemini
>>>>>>> b9cd0ce (Initial commit: LangChain RAG API with semantic/exact query and indexing)
   ```
2. Instala las dependencias y levanta el servidor:
   ```bash
   pip install -r requirements.txt
   uvicorn src.app.main:app --reload
   ```
   
### Despliegue con Docker

1. Asegúrate de tener tu archivo `.env` en la carpeta `config/` con las variables necesarias.
2. Levanta todo el stack (API + base de datos) con:

   ```bash
   docker-compose up --build
   ```

3. La API estará disponible en [http://localhost:8000](http://localhost:8000)

## Descripción de archivos principales

### src/app/
- **main.py**: Define la API REST con FastAPI, incluyendo los endpoints para consulta exacta (`/rag/query_exact`), semántica (`/rag/query_semantic`) e indexado (`/rag/index`).
- **dependencies/**: Proporciona funciones para obtener instancias singleton de los componentes principales (`Retriever` e `Indexer`).
- **db/**: Lógica de conexión a la base de datos PostgreSQL y utilidades como logging de queries.
- **schemas/**: Modelos de datos (Pydantic) para las peticiones y respuestas de la API.
- **middleware/**: Middlewares como el de logging de peticiones y respuestas.

### src/cache/
- **cache_manager.py**: Lógica para cache exacto y semántico, desacoplada del Retriever.

### src/indexer/
- **indexer.py**: Lógica para generar embeddings de documentos y almacenarlos en la base de datos usando Google Gemini y pgvector.

### src/retriever/
- **retriever.py**: Lógica de recuperación RAG. Busca documentos relevantes, gestiona embeddings y consulta el LLM de Gemini para generar respuestas.

### tests/
- **test_api.py**: Pruebas automáticas para los endpoints principales de la API usando FastAPI TestClient.
- **test_indexer.py**: Pruebas unitarias para la lógica de indexado de documentos.
- **test_retriever.py**: Pruebas unitarias para la lógica de recuperación y generación de respuestas.

### docs/
- **cache_types.md**: Explicación detallada de la diferencia entre exact cache y semantic cache. Consulta este archivo para entender cuándo usar cada tipo de cache y sus ventajas.

- La tabla `prompt_cache` ahora incluye los campos `context` (texto del contexto usado), `context_hash` (hash SHA256 del contexto para comparación robusta) y `prompt_embedding` (embedding del prompt como tipo vector). Si tienes una base de datos previa, deberás migrar la estructura para añadir estos campos.

## Seguridad

Esta API no requiere autenticación. Los endpoints son públicos, pero están protegidos contra abuso mediante rate limiting y CORS. No se almacena información de usuario.