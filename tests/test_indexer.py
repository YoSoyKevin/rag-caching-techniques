import pytest
from src.indexer.indexer import Indexer

class DummyEmbeddings:
    def embed_documents(self, docs):
        return [[0.1]*768 for _ in docs]

class DummySession:
    def __init__(self):
        self.inserted = []
        self.committed = False
        self.rolled_back = False
    def execute(self, *args, **kwargs):
        self.inserted.append((args, kwargs))
    def commit(self):
        self.committed = True
    def rollback(self):
        self.rolled_back = True
    def close(self):
        pass

def dummy_get_db_session():
    return DummySession()

def test_index_documents(monkeypatch):
    indexer = Indexer()
    indexer.embeddings = DummyEmbeddings()
    monkeypatch.setattr("src.indexer.indexer.get_db_session", dummy_get_db_session)
    count = indexer.index_documents(["doc1", "doc2"])
    assert count == 2 