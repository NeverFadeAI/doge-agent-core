import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from aiologger import Logger
from aiologger.handlers.files import AsyncFileHandler
from aiologger.formatters.base import Formatter


def setup_sync_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

    file_handler = TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=7, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def setup_async_logger(name, log_file, level=logging.INFO):
    formatter = Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

    file_handler = AsyncFileHandler(filename=log_file)
    file_handler.formatter = formatter

    logger = Logger(name=name, level=level)
    logger.add_handler(file_handler)

    return logger


# 创建日志目录
if not os.path.exists('logs'):
    os.mkdir('logs')

# 初始化同步日志记录器
app_logger = setup_sync_logger('app', 'logs/app.log')
error_logger = setup_sync_logger('error', 'logs/error.log', level=logging.ERROR)
test_logger = setup_sync_logger('test', 'logs/test.log')

# 异步日志记录器
async_app_logger = setup_async_logger('async_app', 'logs/async_app.log')
async_error_logger = setup_async_logger('async_error', 'logs/async_error.log', level=logging.ERROR)
async_test_logger = setup_async_logger('async_test', 'logs/async_test.log')

