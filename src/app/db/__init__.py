import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import json

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../config/.env'))

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    try:
        db = SessionLocal()
        return db
    except SQLAlchemyError as e:
        raise RuntimeError(f"Error connecting to DB: {e}")

def log_query(session, endpoint: str, request_body: bytes, response: str, status_code: int):
    try:
        from sqlalchemy import text
        request_json = request_body.decode('utf-8') if request_body else '{}'
        try:
            json.loads(response)
            response_json = response
        except Exception:
            response_json = '{}'
        session.execute(
            text("""
                INSERT INTO query_logs (endpoint, request, response, status_code)
                VALUES (:endpoint, :request, :response, :status_code)
            """),
            {
                "endpoint": endpoint,
                "request": request_json,
                "response": response_json,
                "status_code": status_code
            }
        )
        session.commit()
    except Exception as e:
        session.rollback()
        raise e 