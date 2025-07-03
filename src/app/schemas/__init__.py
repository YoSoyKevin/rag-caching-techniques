from pydantic import BaseModel, Field
from typing import List, Optional, Any

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    result: str
    elapsed: float

class IndexRequest(BaseModel):
    documents: List[str]

class IndexResponse(BaseModel):
    indexed: int

class ExactCacheResponse(BaseModel):
    result: str
    cache_status: str
    elapsed: float

class SemanticCacheResponse(BaseModel):
    result: str
    cache_status: str
    min_distance: float
    elapsed: float 