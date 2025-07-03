import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from sqlalchemy import text
from src.app.db import get_db_session
from dotenv import load_dotenv
from loguru import logger
import json
import time
import hashlib
from src.cache.cache_manager import SemanticCacheManager
from src.app.utils import to_pgvector_str

load_dotenv(os.path.join(os.path.dirname(__file__), '../../config/.env'))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/embedding-001")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
TOP_K = 4
CACHE_DISTANCE_THRESHOLD = float(os.getenv("CACHE_DISTANCE_THRESHOLD", "-0.95"))

class Retriever:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
        self.llm = ChatGoogleGenerativeAI(model=LLM_MODEL)
        self.semantic_cache = SemanticCacheManager()

    def _get_context_from_documents(self, session, query_vector):
        sql = text(f'''
            SELECT content, embedding <#> vector(:query_vector) AS distance
            FROM documents
            ORDER BY distance ASC
            LIMIT {TOP_K}
        ''')
        results = session.execute(sql, {"query_vector": to_pgvector_str(query_vector)}).fetchall()
        context = "\n\n".join([row[0] for row in results])
        return context

    def _hash_context(self, context: str) -> str:
        return hashlib.sha256(context.encode('utf-8')).hexdigest()

    def query(self, prompt: str):
        session = get_db_session()
        start = time.perf_counter()
        try:
            query_vector = self.embeddings.embed_query(prompt)
            context = self._get_context_from_documents(session, query_vector)
            context_hash = self._hash_context(context)
            # Usar SemanticCacheManager para buscar en cache
            cached_response, min_distance = self.semantic_cache.get(
                prompt, query_vector, context_hash
            )
            if cached_response is not None:
                elapsed = time.perf_counter() - start
                return cached_response, "hit", min_distance, elapsed
            # Si no hay cache hit, invocar LLM
            logger.info(f"CACHE MISS: prompt='{prompt[:30]}...', min_distance={min_distance}, context_hash={context_hash[:8]}...")
            messages = [
                ("system", """ Eres un asistente experto, diseñado para brindar respuestas útiles, seguras y respetuosas, en todo momento.

Si el usuario inicia la conversación con un saludo o comentario informal, responde de forma cordial, empática y natural.

Si el usuario formula una pregunta, responde únicamente usando la información contenida en el contexto proporcionado.  
Si el contexto no contiene la respuesta o no es suficiente para responder con precisión, informa educadamente que no dispones de esa información.

Bajo ningún motivo debes:
- Inventar o asumir datos que no estén explícitamente en el contexto.
- Proporcionar información falsa, ambigua o sin sustento.
- Ofrecer diagnósticos médicos, legales o financieros sin un profesional calificado.
- Facilitar actividades peligrosas, ilegales, discriminatorias o poco éticas.
- Compartir o inferir información sensible o personal del usuario u otras personas.
- Promover discursos de odio, violencia o desinformación.

Tus respuestas deben ser claras, responsables, imparciales y centradas en el bienestar del usuario. Siempre prioriza la seguridad, la equidad, la transparencia y el respeto a la privacidad.

Si detectas una posible mala interpretación, riesgo o mal uso de la información solicitada, responde con cautela o rechaza la petición de forma razonada y educada.
"""),
                ("human", f"Contexto:\n{context}\n\nPregunta: {prompt}")
            ]
            response = self.llm.invoke(messages)
            # Guardar en el semantic_cache
            self.semantic_cache.set(
                prompt, query_vector, context, context_hash, response.content
            )
            session.commit()
            elapsed = time.perf_counter() - start
            logger.info(f"Respuesta generada y cacheada para prompt='{prompt[:30]}...' en {elapsed:.2f}s")
            return response.content, "miss", min_distance, elapsed
        except Exception as e:
            session.rollback()
            logger.error(f"Error en Retriever.query: {e}", exc_info=True)
            raise e
        finally:
            session.close() 