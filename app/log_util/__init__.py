"""
全局日志处理器
- 同时输出到终端 (stdout) 和按大小分隔的文件
- 优先级: 环境变量 > config.yml > 默认值

环境变量:
    LOG_LEVEL      日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    LOG_FILE       日志文件路径
    LOG_MAX_BYTES  单个文件最大字节数 (默认 10MB)
    LOG_BACKUPS    保留的备份文件数 (默认 5)
    LOG_CONSOLE    是否输出到终端 (true/false)
    LOG_FILE_OUT   是否输出到文件 (true/false)

用法:
    from app.log_util import logger

    logger.info("这是一条日志")
    logger.error("出错了", exc_info=True)

    # 按模块获取子 logger
    from app.log_util import get_logger
    sub = get_logger("my_module")
    sub.debug("模块级日志")
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.load_config import config

# ---------- 参数解析 ----------

LOG_LEVEL_STR = (
    config.get("logging", "level", env="LOG_LEVEL", default="INFO")
).upper()

LOG_FILE = Path(
    config.get("logging", "file", env="LOG_FILE", default="logs/app.log")
)

LOG_MAX_BYTES = config.get_int(
    "logging", "max_bytes", env="LOG_MAX_BYTES", default=10 * 1024 * 1024
)

LOG_BACKUP_COUNT = config.get_int(
    "logging", "backups", env="LOG_BACKUPS", default=5
)

LOG_CONSOLE = config.get_bool(
    "logging", "console", env="LOG_CONSOLE", default=True
)

LOG_FILE_OUT = config.get_bool(
    "logging", "file_out", env="LOG_FILE_OUT", default=True
)

LOG_FORMAT = config.get(
    "logging", "format", env="LOG_FORMAT",
    default="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
)

LOG_DATE_FORMAT = config.get(
    "logging", "date_format", env="LOG_DATE_FORMAT", default="%Y-%m-%d %H:%M:%S",
)

# ---------- 初始化全局 Logger ----------

def _setup_logger() -> logging.Logger:
    """配置根 logger，避免重复添加 handler"""
    root = logging.getLogger()

    # 避免重复初始化
    if getattr(_setup_logger, "_initialized", False):
        return root

    level = getattr(logging, LOG_LEVEL_STR, logging.INFO)
    root.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

    # --- 控制台 handler ---
    if LOG_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    # --- 文件 handler (按大小分隔) ---
    if LOG_FILE_OUT:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=str(LOG_FILE),
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    root.info("日志系统初始化完成 (level=%s, file=%s, console=%s, file_out=%s)",
              LOG_LEVEL_STR, LOG_FILE, LOG_CONSOLE, LOG_FILE_OUT)

    _setup_logger._initialized = True
    return root


logger = _setup_logger()


def get_logger(name: str) -> logging.Logger:
    """按模块名获取子 logger"""
    return logging.getLogger(name)


__all__ = ["logger", "get_logger"]
