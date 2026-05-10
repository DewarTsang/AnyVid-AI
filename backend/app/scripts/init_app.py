import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.config.setting import settings
from app.core.logger import log
from app.scripts.initialize import InitializeData
from app.utils.common_util import import_module
from app.utils.console import console_close, console_run


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    try:
        await InitializeData().init_db()
        log.info(f"✅ {settings.DATABASE_TYPE}数据库初始化完成")

        from app.common.enums import EnvironmentEnum

        console_run(
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            reload=settings.ENVIRONMENT == EnvironmentEnum.DEV,
            database_ready=True,
        )
    except Exception as e:
        log.error(f"❌ 应用初始化失败: {e!s}")
        raise SystemExit(1)

    yield

    try:
        from app.utils.downloader import downloader

        download_dir = downloader.DOWNLOAD_DIR
        if os.path.exists(download_dir):
            for f in os.listdir(download_dir):
                try:
                    os.remove(os.path.join(download_dir, f))
                except OSError:
                    pass
        console_close()
    except Exception as e:
        log.error(f"❌ 应用关闭过程中发生错误: {e!s}")


def register_middlewares(app: FastAPI) -> None:
    """
    注册全局中间件。

    参数:
    - app (FastAPI): FastAPI 应用实例。

    返回:
    - None
    """
    for middleware in settings.MIDDLEWARE_LIST[::-1]:
        if not middleware:
            continue
        middleware = import_module(middleware, desc="中间件")
        app.add_middleware(middleware)


def register_routers(app: FastAPI) -> None:
    from app.api import router

    app.include_router(router)
