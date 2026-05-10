from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp

from app.config.setting import settings


class CustomCORSMiddleware(CORSMiddleware):
    """CORS跨域中间件"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(
            app,
            allow_origins=settings.ALLOW_ORIGINS,
            allow_methods=settings.ALLOW_METHODS,
            allow_headers=settings.ALLOW_HEADERS,
            allow_credentials=settings.ALLOW_CREDENTIALS,
            expose_headers=settings.CORS_EXPOSE_HEADERS,
        )


class CustomGZipMiddleware(GZipMiddleware):
    """GZip压缩中间件"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(
            app,
            minimum_size=settings.GZIP_MIN_SIZE,
            compresslevel=settings.GZIP_COMPRESS_LEVEL,
        )
