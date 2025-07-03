from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger
from src.app.db import get_db_session, log_query
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_body = await request.body()
        logger.info(f"Request: {request.url.path} - Body: {request_body}")
        
        response = await call_next(request)
        
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        try:
            session = get_db_session()
            log_query(
                session,
                endpoint=str(request.url),
                request_body=request_body,
                response=response_body.decode(),
                status_code=response.status_code
            )
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        ) 