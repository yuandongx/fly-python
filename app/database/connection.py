"""
数据库连接管理
- 基于 pymongo 连接池，最小化资源占用
- 惰性连接：仅在实际访问时初始化
- 环境变量优先，配置文件兜底
"""
import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from .config import config

logger = logging.getLogger("database")

# ---------- 连接参数 ----------
# 环境变量: MONGODB_URI / MONGODB_HOST / MONGODB_PORT / MONGODB_USER / MONGODB_PASSWORD
# 配置文件: database.uri / database.host / database.port / database.user / database.password / database.db

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 27017


def _build_uri() -> str:
    """构造 MongoDB 连接 URI"""
    # 显式 URI 优先
    uri = config.get("MONGODB_URI") or config.get("uri")
    if uri:
        return str(uri)

    host = config.get("MONGODB_HOST") or config.get("host") or _DEFAULT_HOST
    port = config.get_int("MONGODB_PORT") or config.get_int("port") or _DEFAULT_PORT
    user = config.get("MONGODB_USER") or config.get("user")
    password = config.get("MONGODB_PASSWORD") or config.get("password")
    db = config.get("MONGODB_DB") or config.get("db")

    if user and password:
        auth = f"{user}:{password}@"
    else:
        auth = ""

    base = f"mongodb://{auth}{host}:{port}/"
    if db:
        base += f"{db}"
    return base


class ConnectionManager:
    """MongoDB 连接管理器

    特性:
    - 惰性初始化，首次使用时才建立连接
    - pymongo 内置连接池 (minPoolSize=0, maxPoolSize 可配)
    - 自动重连
    """

    def __init__(self):
        self._client: Optional[MongoClient] = None

    @property
    def client(self) -> MongoClient:
        if self._client is None:
            self._connect()
        assert self._client is not None
        return self._client

    def _connect(self) -> None:
        uri = _build_uri()

        # 连接池参数，实现最小化资源占用
        max_pool = config.get_int("MONGODB_MAX_POOL_SIZE") or config.get_int("max_pool_size") or 10
        min_pool = config.get_int("MONGODB_MIN_POOL_SIZE") or config.get_int("min_pool_size") or 0
        max_idle_ms = config.get_int("MONGODB_MAX_IDLE_TIME_MS") or config.get_int("max_idle_time_ms") or 60000
        server_timeout_ms = config.get_int("MONGODB_SERVER_TIMEOUT_MS") or config.get_int("server_timeout_ms") or 5000
        connect_timeout_ms = config.get_int("MONGODB_CONNECT_TIMEOUT_MS") or config.get_int("connect_timeout_ms") or 5000

        try:
            self._client = MongoClient(
                uri,
                maxPoolSize=max_pool,
                minPoolSize=min_pool,             # 0 = 无活跃请求时不保活连接
                maxIdleTimeMS=max_idle_ms,        # 空闲连接超时回收
                serverSelectionTimeoutMS=server_timeout_ms,
                connectTimeoutMS=connect_timeout_ms,
                # 读写关注降低开销
                w=config.get("w") or 1,
                readPreference=config.get("read_preference") or "primaryPreferred",
            )
            # 触发一次探测 (验证连接可用)
            self._client.admin.command("ping")
            logger.info("MongoDB 连接池已建立 → %s (pool: %d-%d)", uri, min_pool, max_pool)
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("MongoDB 连接失败: %s", e)
            self._client = None
            raise

    def get_database(self, db_name: str = None):
        """获取数据库实例"""
        target = db_name or config.get("MONGODB_DB") or config.get("db") or "fly_python"
        return self.client.get_database(target)

    def get_collection(self, collection: str, db_name: str = None):
        """获取集合实例"""
        return self.get_database(db_name).get_collection(collection)

    def close(self) -> None:
        """关闭连接池"""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("MongoDB 连接池已关闭")

    def is_connected(self) -> bool:
        if self._client is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False


# 全局单例
connection = ConnectionManager()
