"""
认证接口 — 登录 / 登出

密码校验: MD5( 数据库密码 + 秒级时间整除10 + -1/0/+1 ), 客户端与服务端各自计算后匹配

URL:
    POST   /api/auth/login         登录 (获取 session_key)
    POST   /api/auth/logout        登出 (销毁 session)
"""
import uuid
import hashlib
from typing import Optional
import time
import redis

from pydantic import BaseModel

from app.server.handlers._base import BaseHandler
from app.load_config import config
from app.log_util import get_logger

logger = get_logger("auth")

# ============================
# Redis 会话管理
# ============================

REDIS_HOST = config.get("redis", "host", env="REDIS_HOST", default="127.0.0.1")
REDIS_PORT = config.get_int("redis", "port", env="REDIS_PORT", default=6379)
REDIS_DB = config.get_int("redis", "db", env="REDIS_DB", default=10)
REDIS_PASSWORD = config.get("redis", "password", env="REDIS_PASSWORD", default=None)
SESSION_TTL = config.get_int("redis", "session_ttl", env="SESSION_TTL", default=86400)  # 默认 24 小时

_redis_client: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    """懒加载 Redis 连接"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD or None,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        try:
            _redis_client.ping()
            logger.info("Redis 连接成功: %s:%d/%d", REDIS_HOST, REDIS_PORT, REDIS_DB)
        except Exception as exc:
            logger.warning("Redis 连接失败: %s, 会话将无法缓存", exc)
    return _redis_client


def _session_redis_key(username: str, ip: str) -> str:
    """Redis key: session:{username}:{ip}"""
    return f"session:{username}:{ip}"


def _session_user_key(session_key: str) -> str:
    """Redis key: session_key:{sk} → username"""
    return f"session_key:{session_key}"


# ============================
# 密码工具 — 动态 MD5
# ============================

def _md5_password(password: str) -> str:
    """密码哈希 (MD5)"""
    return hashlib.md5(password.encode()).hexdigest()


def _dynamic_password(db_password: str) -> list[str]:
    """生成当前时间窗口内的 3 个动态密码: MD5( db_password + t ) , t ∈ {T-1, T, T+1}, T = int(time/10)"""
    t0 = int(time.time() / 10)
    return [_md5_password(f"{db_password}+{t}") for t in (t0 - 1, t0, t0 + 1)]


# ============================
# LoginHandler
# ============================

class LoginHandler(BaseHandler):
    NAME = "auth/login"
    COLLECTION = "login"
    ALLOW_METHOD = ["POST"]

    def get_session_key(self, username: str, password: str, ip: str) -> Optional[str]:
        """校验凭证并返回 session_key

        1. 优先查 Redis 缓存 (by username+ip)
        2. 缓存未命中则查 MongoDB 验证密码
        3. 验证通过后生成 session_key, 写入 Redis 并返回
        """

        # ---- Step 1: 查 Redis 缓存 ----
        try:
            r = _get_redis()
            cache_key = _session_redis_key(username, ip)
            cached = r.get(cache_key)
            if cached:
                logger.info("会话缓存命中: user=%s ip=%s", username, ip)
                # 刷新 TTL
                r.expire(cache_key, SESSION_TTL)
                r.expire(_session_user_key(cached), SESSION_TTL)
                return cached
        except Exception as exc:
            logger.warning("Redis 读取异常, 降级到数据库校验: %s", exc)

        # ---- Step 2: 校验密码 (MongoDB) ----
        doc = self.crud.find_one({"username": username})
        if not doc:
            logger.info("登录失败: user=%s ip=%s (用户名或密码错误)", username, ip)
            return None
        
        pk = _dynamic_password(doc.get("password", ""))
        if password not in pk:
            logger.info("登录失败: user=%s ip=%s (用户名或密码错误)", username, ip)
            return None

        # ---- Step 3: 生成 session_key 并写 Redis ----
        session_key = uuid.uuid4().hex
        try:
            r = _get_redis()
            pipe = r.pipeline()
            pipe.setex(_session_redis_key(username, ip), SESSION_TTL, session_key)
            pipe.setex(_session_user_key(session_key), SESSION_TTL, username)
            pipe.execute()
            logger.info("登录成功: user=%s ip=%s", username, ip)
        except Exception as exc:
            logger.warning("Redis 写入失败, 仍返回 session_key (未缓存): %s", exc)

        return session_key

    def post(self, data: dict, request=None, **kwargs) -> dict:
        """POST /api/auth/login"""
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        # 从 Request 对象获取客户端 IP (支持反向代理)
        ip = ""
        if request is not None:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip = forwarded.split(",")[0].strip()
            else:
                ip = request.client.host if request.client else ""

        if not username or not password:
            return {"error": "username and password are required"}


        session_key = self.get_session_key(username, password, ip)
        if not session_key:
            return {"error": "username or password is incorrect"}

        return {"session_key": session_key}


# ============================
# LogoutHandler
# ============================

class LoginItem(BaseModel):
    username: str
    password: str

class LogoutHandler(BaseHandler):
    NAME = "auth/logout"
    COLLECTION = "login"
    ALLOW_METHOD = ["POST"]
    BODY_MODEL = LoginItem

    def post(self, data: dict) -> dict:
        """POST /api/auth/logout — 销毁会话"""
        username = data.get("username", "").strip()
        session_key = data.get("session_key", "").strip()

        if not username or not session_key:
            return {"error": "username and session_key are required"}

        try:
            r = _get_redis()
            # 校验 session_key 所属用户
            owner = r.get(_session_user_key(session_key))
            if owner != username:
                return {"error": "invalid session_key"}

            # 删除两条 Redis key
            pipe = r.pipeline()
            pipe.delete(_session_redis_key(username, ""))  # 清空该用户所有 ip 的 session
            pipe.delete(_session_user_key(session_key))
            pipe.execute()
            logger.info("登出成功: user=%s", username)
        except Exception as exc:
            logger.warning("Redis 操作异常, 登出降级: %s", exc)

        return {"message": "logout success"}
