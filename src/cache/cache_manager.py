import os
from src.app.db import get_db_session
from sqlalchemy import text
import hashlib
from loguru import logger
from src.app.utils import to_pgvector_str

# Para <#> (negative dot product), valores más negativos = mayor similitud
CACHE_DISTANCE_THRESHOLD = float(os.getenv("CACHE_DISTANCE_THRESHOLD", "-0.95"))

class ExactCacheManager:
    def get(self, prompt: str):
        session = get_db_session()
        try:
            sql = text("SELECT response FROM exact_cache WHERE prompt = :prompt LIMIT 1")
            row = session.execute(sql, {"prompt": prompt}).fetchone()
            if row:
                logger.info(f"ExactCache HIT for prompt: {prompt[:30]}...")
                return row[0]
            return None
        finally:
            session.close()

    def set(self, prompt: str, response: str):
        session = get_db_session()
        try:
            insert_sql = text("INSERT INTO exact_cache (prompt, response) VALUES (:prompt, :response)")
            session.execute(insert_sql, {"prompt": prompt, "response": response})
            session.commit()
            logger.info(f"ExactCache SET for prompt: {prompt[:30]}...")
        finally:
            session.close()

class SemanticCacheManager:
    def get(self, prompt: str, prompt_embedding, context_hash: str, threshold: float = None):
        session = get_db_session()
        try:
            # Usar threshold de entorno si no se pasa explícito
            th = threshold if threshold is not None else CACHE_DISTANCE_THRESHOLD
            
            sql = text('''
                SELECT response, prompt_embedding, prompt_embedding <#> vector(:query_vector) AS distance
                FROM semantic_cache
                ORDER BY distance ASC
                LIMIT 5
            ''')
            
            logger.debug(f"Using threshold: {th}")
    
            results = session.execute(sql, {
                "query_vector": to_pgvector_str(prompt_embedding)
            }).fetchall()
            
            if not results:
                logger.info("SemanticCache MISS: No results found")
                return None, None
                
            response, cached_vector, distance = results[0]
            
            # Para <#>: valores más negativos indican mayor similitud
            # Verificamos si la distancia es menor que el threshold (más negativa = más similar)
            if distance <= th:
                similarity_percentage = (1 + distance) * 50  # Convierte a porcentaje aproximado
                logger.info(f"SemanticCache HIT: distance={distance:.4f} (~{similarity_percentage:.1f}% similarity)")
                return response, distance
            else:
                similarity_percentage = (1 + distance) * 50
                logger.info(f"SemanticCache MISS: distance={distance:.4f} (~{similarity_percentage:.1f}% similarity) > threshold={th}")
                return None, distance
                
        except Exception as e:
            logger.error(f"Error in SemanticCache get: {e}")
            return None, None
        finally:
            session.close()

    def set(self, prompt: str, prompt_embedding, context: str, context_hash: str, response: str):
        session = get_db_session()
        try:
            insert_sql = text('''
                INSERT INTO semantic_cache (prompt, prompt_embedding, context, context_hash, response)
                VALUES (:prompt, :prompt_embedding, :context, :context_hash, :response)
            ''')
            session.execute(insert_sql, {
                "prompt": prompt,
                "prompt_embedding": prompt_embedding,
                "context": context,
                "context_hash": context_hash,
                "response": response
            })
            session.commit()
            logger.info(f"SemanticCache SET for prompt: {prompt[:30]}...")
        except Exception as e:
            logger.error(f"Error in SemanticCache set: {e}")
            raise
        finally:
            session.close()

    def get_similarity_percentage(self, distance: float) -> float:
        """
        Convierte la distancia del operador <#> a un porcentaje de similitud aproximado
        Para <#>: -1.0 = 100% similar, 0.0 = 50% similar, 1.0 = 0% similar
        """
        return max(0, min(100, (1 + distance) * 50))