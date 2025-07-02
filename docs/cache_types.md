# Tipos de Cache en RAG API

## Exact Cache (Prompt Caching)

- **Definición:** Guarda y recupera respuestas solo si el prompt recibido es exactamente igual (caracter por caracter) a uno previamente almacenado.
- **Uso:** Ideal para prompts frecuentes, plantillas fijas o cuando se requiere una respuesta determinística.
- **Ventajas:**
  - Respuestas instantáneas para prompts repetidos.
  - No hay ambigüedad: solo hay hit si el prompt es idéntico.
- **Ejemplo:**
  - Prompt: `¿Cuál es la capital de Francia?`
  - Si existe exactamente ese prompt en cache, se devuelve la respuesta cacheada.
  - Si el usuario escribe `¿Cual es la capital de Francia?` (sin tilde), **no hay hit**.

---

## Semantic Cache (Semantic Caching)

- **Definición:** Guarda y recupera respuestas para prompts que sean semánticamente similares, usando embeddings y búsqueda vectorial. 
- **Uso:** Ideal para preguntas similares en significado, aunque no sean idénticas en texto.
- **Ventajas:**
  - Responde rápido a variaciones de una misma pregunta.
  - Reduce el costo de procesamiento para prompts parecidos.
- **Criterio de hit:**
  - Solo se considera hit si la distancia coseno del embedding más cercano está entre -1 y el threshold configurado (por defecto -0.95).
  - Si no hay ningún resultado en ese rango, es miss y se genera una nueva respuesta.
- **Ejemplo:**
  - Prompt cacheado: `¿Cuál es la capital de Francia?`
  - Nuevo prompt: `¿Me puedes decir la capital de Francia?`
  - Si el embedding es suficientemente similar (por ejemplo, distancia -0.98), **hay hit** y se devuelve la respuesta cacheada.
  - Si la distancia es -0.7, **no hay hit**.

---

## Resumen visual

| Tipo de cache   | Búsqueda por         | Hit para variantes | Uso recomendado                |
|-----------------|----------------------|--------------------|-------------------------------|
| Exact cache     | Prompt (string)      | No                 | Prompts fijos, respuestas exactas |
| Semantic cache  | Embedding (coseno)   | Sí, si distancia entre -1 y threshold | Preguntas similares, contexto relevante | 
