
from app.core.logger import async_error_logger,async_app_logger
import asyncio
from functools import wraps


# 异步重试装饰器
def async_retry(retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:  # 最后一次尝试
                        await async_error_logger.error(f"All retry attempts failed: {str(e)}")
                        raise
                    await async_error_logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    await asyncio.sleep(delay)
            return await func(*args, **kwargs)  # 最后一次尝试
        return wrapper
    return decorator