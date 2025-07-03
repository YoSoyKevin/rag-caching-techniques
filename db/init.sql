-- Crear extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla para documentos y embeddings
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsquedas vectoriales
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Tabla para logging de queries
CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    request JSONB,
    response JSONB,
    status_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para almacenamiento de respuestas para semantic cache
CREATE TABLE IF NOT EXISTS public.semantic_cache (
    id SERIAL PRIMARY KEY,

    -- Texto del prompt original del usuario
    prompt TEXT NOT NULL,

    -- Embedding del prompt, para hacer búsqueda semántica
    prompt_embedding vector(768) NOT NULL,

    -- Texto del contexto usado para generar la respuesta
    context TEXT NOT NULL,

    -- Hash SHA256 del contexto, para verificar si sigue siendo el mismo
    context_hash TEXT NOT NULL,

    -- Respuesta generada por el LLM
    response TEXT NOT NULL,

    -- Timestamp automático
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsquedas vectoriales en la tabla de semantic_cache
CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding ON semantic_cache USING ivfflat (prompt_embedding vector_cosine_ops) WITH (lists = 100);

-- Tabla para almacenamiento de respuestas para exact cache
CREATE TABLE IF NOT EXISTS public.exact_cache (
    id SERIAL PRIMARY KEY,

    -- Prompt exacto que ingresó el usuario
    prompt TEXT NOT NULL,

    -- Respuesta generada por el LLM en su momento
    response TEXT NOT NULL,

    -- Timestamp de creación
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice por prompt para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_exact_cache_prompt ON public.exact_cache (prompt);