import pytest
from src.retriever.retriever import Retriever

class DummyEmbeddings:
    def embed_query(self, prompt):
        return [0.1]*768

class DummyLLM:
    def invoke(self, messages):
        return type('obj', (object,), {"content": "Respuesta LLM simulada"})()

class DummySession:
    def execute(self, sql, params):
        class Row:
            def __getitem__(self, idx):
                return "doc context" if idx == 0 else 0.0
        
        class MockResult:
            def fetchall(self):
                return [Row(), Row()]

        return MockResult()

    def close(self):
        pass

    def rollback(self):
        pass

    def commit(self):
        pass

def dummy_get_db_session():
    return DummySession()

def test_query(monkeypatch):
    retriever = Retriever()
    retriever.embeddings = DummyEmbeddings()
    retriever.llm = DummyLLM()
    monkeypatch.setattr("src.retriever.retriever.get_db_session", dummy_get_db_session)
    result = retriever.query("¿Cuál es la capital de Francia?")
    assert isinstance(result, tuple)
    assert "LLM simulada" in result[0] 