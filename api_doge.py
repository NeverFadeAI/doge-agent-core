# -*- coding: utf-8 -*-
# api_doge.py

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

from app.api import routes
from app.core.config import settings
from app.core.logger import app_logger, error_logger, async_app_logger
from app.storage.mysql_manager import setup_database, engine, start_mysql_health_check
from app.storage.redis_manager import setup_redis, close_redis, start_health_check
from app.storage.milvus_manager import setup_milvus, close_milvus
from app.memory.chat_history_manager import ChatHistory
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import uvicorn



@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Application is starting up")
    try:
        await setup_database()
        start_mysql_health_check(app)
        app.state.redis_manager = await setup_redis()
        start_health_check(app)

        app.state.milvus_manager = await setup_milvus(
            settings.OPENAI_APIKEY,
            redis=app.state.redis_manager,
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )

        app.state.chat_history = ChatHistory(
            app.state.redis_manager,
            app.state.milvus_manager
        )

        # 根据操作系统设置信号处理
        if sys.platform != "win32":
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(graceful_shutdown(app, s))
                )
            app_logger.info("Signal handlers registered for non-Windows platform")
        else:
            app_logger.info("Running on Windows, signal handlers are not supported")

    except Exception as e:
        error_logger.exception(f"Error during startup: {e}")
        raise
    yield
    app_logger.info("Application is shutting down")


async def graceful_shutdown(app: FastAPI, sig: signal.Signals = None):
    if sig:
        app_logger.info(f"Received signal {sig.name} to shut down")
    else:
        app_logger.info("Initiating graceful shutdown")

    await close_redis(app)
    await close_milvus(app)
    await engine.dispose()
    await async_app_logger.info("Graceful shutdown completed")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.include_router(routes.router, prefix=settings.API_V1_STR, tags=["agents"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_logger.exception(f"main Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal Server Error:{str(exc)}"}
    )


async def start_server():
    try:
        config = uvicorn.Config(app, host="0.0.0.0", port=5077)
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        error_logger.exception(f"Error starting server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error:{str(e)}")


if __name__ == "__main__":
    app_logger.info("Starting application")
    asyncio.run(start_server())