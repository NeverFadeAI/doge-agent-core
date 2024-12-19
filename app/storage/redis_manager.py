# app/db/redis_manager.py

import asyncio
from typing import Optional
import aioredis
from app.core.config import settings
from app.core.logger import app_logger, error_logger, async_error_logger
from contextlib import asynccontextmanager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class RedisManager:
    _instance = None
    _redis_pool = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.init_pool()
        return cls._instance

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(aioredis.RedisError)
    )
    async def init_pool(self):
        try:
            self._redis_pool = aioredis.ConnectionPool.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                password=settings.REDIS_PWD,
                decode_responses=True,
                encoding="utf-8",
                max_connections=settings.REDIS_POOL_SIZE,
                # Remove the timeout parameter from here
            )
            self._redis = aioredis.Redis(
                connection_pool=self._redis_pool,
                socket_timeout=settings.REDIS_TIMEOUT  # Add timeout here
            )
            app_logger.info("Redis connection pool initialized successfully")
        except Exception as e:
            error_logger.exception(f"Failed to initialize Redis connection pool: {e}")
            raise

    async def close(self):
        if self._redis_pool:
            await self._redis_pool.disconnect()
            app_logger.info("Redis connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        if not self._redis_pool:
            await self.init_pool()
        try:
            yield self._redis
        except aioredis.RedisError as e:
            await async_error_logger.exception(f"Error while getting Redis connection: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def set(self, key: str, value: str, ex: Optional[int] = None):
        async with self.get_connection() as conn:
            await conn.set(key, value, ex=ex)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def get(self, key: str):
        async with self.get_connection() as conn:
            return await conn.get(key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def delete(self, key: str):
        async with self.get_connection() as conn:
            return await conn.delete(key)

    async def health_check(self):
        try:
            return await self._redis.ping()
        except aioredis.RedisError:
            error_logger.exception("Redis health check failed")
            return False

    async def execute_pipeline(self, commands):
        async with self.get_connection() as conn:
            pipeline = conn.pipeline(transaction=False)
            for cmd, *args in commands:
                getattr(pipeline, cmd)(*args)
            return await pipeline.execute()


async def setup_redis():
    redis_manager = await RedisManager.get_instance()
    app_logger.info("Redis setup completed")
    return redis_manager


async def close_redis(app):
    if hasattr(app.state, 'redis_manager'):
        await app.state.redis_manager.close()
    app_logger.info("Redis connections closed")


async def periodic_health_check(app):
    while True:
        try:
            if await app.state.redis_manager.health_check():
                app_logger.info("Redis health check passed")
            else:
                error_logger.error("Redis health check failed")
        except Exception as e:
            error_logger.exception(f"Error during Redis health check: {e}")
        await asyncio.sleep(300)  # 每5分钟检查一次


def start_health_check(app):
    asyncio.create_task(periodic_health_check(app))
