import os
import time
from fastapi import FastAPI, HTTPException, Depends, Query, status, Request
from dotenv import load_dotenv

load_dotenv()
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.app.dependencies import get_retriever, get_indexer
from src.app.schemas import QueryRequest, QueryResponse, IndexRequest, IndexResponse, ExactCacheResponse, SemanticCacheResponse
from src.app.middleware import LoggingMiddleware
from src.app.db import get_db_session, log_query
import json
from sqlalchemy import text
from src.cache.cache_manager import ExactCacheManager, SemanticCacheManager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# --- RATE LIMITING ---
limiter = Limiter(key_func=get_remote_address)
rate_limiter = limiter.limit

app = FastAPI(title="LangChain RAG API")
app.add_middleware(LoggingMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: PlainTextResponse("Rate limit exceeded", status_code=429))

# --- CORS ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:8000,http://localhost:3000,http://localhost:5173").split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/rag/query_exact", response_model=ExactCacheResponse, tags=["RAG"])
@rate_limiter("5/minute")
def rag_query_exact(request: Request, query_request: QueryRequest, session=Depends(get_db_session), retriever=Depends(get_retriever)):
    start = time.perf_counter()
    response_content = None
    cache_status = "miss"
    status_code = status.HTTP_200_OK
    try:
        prompt = query_request.prompt
        sql = text("SELECT response FROM exact_cache WHERE prompt = :prompt LIMIT 1")
        row = session.execute(sql, {"prompt": prompt}).fetchone()
        if row:
            response_content = row[0]
            cache_status = "hit"
        else:
            response = retriever.llm.invoke([("human", prompt)])
            response_content = response.content
            insert_sql = text("INSERT INTO exact_cache (prompt, response) VALUES (:prompt, :response)")
            session.execute(insert_sql, {"prompt": prompt, "response": response_content})
            session.commit()
        elapsed = round((time.perf_counter() - start) * 1000)  # Convertir a milisegundos y redondear a entero
        return ExactCacheResponse(result=response_content, cache_status=cache_status, elapsed=elapsed)
    except Exception as e:
        session.rollback()
        logger.error(f"Error en /rag/query_exact: {e}", exc_info=True)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail="Internal server error")
    finally:
        log_query(session, "/rag/query_exact", query_request.json().encode('utf-8'), json.dumps({"result": response_content, "cache_status": cache_status}), status_code)

@app.post("/rag/query_semantic", response_model=SemanticCacheResponse, tags=["RAG"])
@rate_limiter("5/minute")
def rag_query_semantic(request: Request, query_request: QueryRequest, retriever=Depends(get_retriever), session=Depends(get_db_session)):
    result_content = None
    cache_status = "miss"
    min_distance = None
    status_code = status.HTTP_200_OK
    start = time.perf_counter()
    try:
        result_content, cache_status, min_distance, _ = retriever.query(query_request.prompt)
        elapsed = round((time.perf_counter() - start) * 1000) # Calcular elapsed aquí y redondear a entero
        return SemanticCacheResponse(result=result_content, cache_status=cache_status, min_distance=min_distance, elapsed=elapsed)
    except Exception as e:
        logger.error(f"Error en /rag/query_semantic: {e}", exc_info=True)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail="Internal server error")
    finally:
        log_query(session, "/rag/query_semantic", query_request.json().encode('utf-8'), json.dumps({"result": result_content, "cache_status": cache_status, "min_distance": min_distance}), status_code)

@app.post("/rag/index", response_model=IndexResponse, tags=["RAG"])
@rate_limiter("2/minute")
def rag_index(request: IndexRequest, indexer=Depends(get_indexer)):
    try:
        count = indexer.index_documents(request.documents)
        return IndexResponse(indexed=count)
    except Exception as e:
        logger.exception("Error en /rag/index")
        raise HTTPException(status_code=500, detail="Internal server error") 
    
@app.get("/health",tags=["STATUS"])
def health_check():
    return {"status": "ok"}    
