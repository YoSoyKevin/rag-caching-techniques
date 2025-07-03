import pytest
from fastapi.testclient import TestClient
from src.app.main import app
from src.app.dependencies import get_retriever
from src.app.db import get_db_session

class DummyRetriever:
    def query(self, prompt):
        return f"Respuesta simulada para: {prompt}"

class DummySession:
    def execute(self, *args, **kwargs): pass
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass

def override_get_retriever():
    return DummyRetriever()

def override_get_db_session():
    return DummySession()

# Aplicar overrides para los tests
app.dependency_overrides[get_retriever] = override_get_retriever
app.dependency_overrides[get_db_session] = override_get_db_session

client = TestClient(app)

def test_rag_query_exact():
    response = client.post("/rag/query_exact", json={"prompt": "¿Cuál es la capital de Francia?"})
    assert response.status_code == 200
    assert isinstance(response.json()["result"], str)
    assert response.json()["result"]  # No vacío

def test_rag_query_semantic():
    response = client.post("/rag/query_semantic", json={"prompt": "¿Cuál es la capital de Francia?"})
    assert response.status_code == 200
    assert isinstance(response.json()["result"], str)
    assert response.json()["result"]  # No vacío 