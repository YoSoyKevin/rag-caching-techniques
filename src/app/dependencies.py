from src.retriever.retriever import Retriever
from src.indexer.indexer import Indexer

_retriever = None
_indexer = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever

def get_indexer():
    global _indexer
    if _indexer is None:
        _indexer = Indexer()
    return _indexer