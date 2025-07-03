import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import text
from src.app.db import get_db_session
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../config/.env'))

EMBEDDING_MODEL = "models/embedding-001"

class Indexer:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    def index_documents(self, documents, metadata=None):
        session = get_db_session()
        try:
            vectors = self.embeddings.embed_documents(documents)
            for i, doc in enumerate(documents):
                meta = metadata[i] if metadata and i < len(metadata) else None
                session.execute(
                    text("""
                        INSERT INTO documents (content, embedding, metadata)
                        VALUES (:content, :embedding, :metadata)
                    """),
                    {
                        "content": doc,
                        "embedding": vectors[i],
                        "metadata": meta
                    }
                )
            session.commit()
            return len(documents)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close() 