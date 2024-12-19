# app/db/mysql_manager.py
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from contextlib import asynccontextmanager
from app.core.config import settings
from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.logger import app_logger, error_logger, async_app_logger, async_error_logger
import aiomysql
import asyncio

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL.replace("mysql+pymysql", "mysql+aiomysql"),
    echo=settings.DB_ECHO,
    future=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 60},  # 增加连接超时时间
    poolclass=sqlalchemy.AsyncAdaptedQueuePool
)

# 创建异步会话
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def get_db_session():
    """异步上下文管理器，用于获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            await async_error_logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def execute_with_retry(session, statement):
    """带重试机制的SQL执行函数"""
    try:
        result = await session.execute(statement)
        return result
    except SQLAlchemyError as e:
        await session.rollback()
        await async_error_logger.error(f"SQL execution error: {str(e)}")
        raise


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((aiomysql.Error, SQLAlchemyError))
)
async def preload_pool():
    """预加载连接池"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        app_logger.info("Database connection pool preloaded successfully")
    except Exception as e:
        error_logger.error(f"Failed to preload database connection pool: {str(e)}")
        raise


async def recycle_connections():
    """回收数据库连接"""
    try:
        await engine.dispose()
        await async_app_logger.info("Database connections recycled successfully")
    except Exception as e:
        await async_error_logger.error(f"Failed to recycle database connections: {str(e)}")


async def setup_database():
    """设置数据库相关的异步任务和调度器"""
    try:
        # 预加载连接池
        await preload_pool()

        # 设置定时任务以回收连接
        scheduler = AsyncIOScheduler()
        scheduler.add_job(recycle_connections, 'interval', hours=1)
        scheduler.start()

        app_logger.info("Database setup completed")
    except Exception as e:
        error_logger.error(f"Database setup failed: {str(e)}")
        # 在这里可以添加适当的错误处理逻辑，比如重试或者退出应用


async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def periodic_health_check(app):
    while True:
        if await health_check():
            app_logger.info("MySQL health check passed")
        else:
            error_logger.error("MySQL health check failed")
        await asyncio.sleep(300)  # 每5分钟检查一次


def start_mysql_health_check(app):
    asyncio.create_task(periodic_health_check(app))
