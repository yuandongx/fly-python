"""
全局配置加载器
- 优先级: 环境变量 > YAML 配置文件 > 默认值
- 单例模式, 整个文件只解析一次

用法:
    from app.load_config import config

    # 1) 获取整个配置段
    db_cfg = config.section("database")        # → {"host": "...", "port": 27017, ...}
    log_cfg = config.section("logging")
    celery_cfg = config.section("celery")

    # 2) 按 key 取值 (env 优先)
    host = config.get("database", "host", env="MONGODB_HOST", default="127.0.0.1")

    # 3) 类型安全
    port = config.get_int("database", "port", env="MONGODB_PORT", default=27017)
    debug = config.get_bool("logging", "debug", env="LOG_DEBUG", default=False)
    urls = config.get_list("spider", "seed_urls", env="SPIDER_SEED_URLS", default=[])
"""
import json
import os
from pathlib import Path
from typing import Any, Optional


# ---------- 配置文件定位 ----------

_CONFIG_DIRS = [
    os.getenv("CONFIG_DIR", "/app"),
    Path(__file__).resolve().parent.parent,   # fly-python/
    Path.cwd(),
]
_CONFIG_FILES = ["config.yml", "config.yaml", "config.json"]


# ---------- 单例加载器 ----------

class ConfigLoader:
    """全局配置加载器

    特性:
    - 首次访问时惰性加载 config.yml / config.json
    - 支持按 section 获取, 环境变量自动覆盖
    - get_int / get_bool / get_list 类型安全读取
    """

    def __init__(self):
        self._raw: dict[str, Any] = {}
        self._loaded: bool = False

    # ---- 加载 ----

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        path = self._find_file()
        print(f"🔍 配置文件路径: {path}")
        if path is None:
            return
        try:
            suffix = path.suffix.lower()
            if suffix in (".yml", ".yaml"):
                import yaml
                with open(path, "r", encoding="utf-8") as fh:
                    self._raw = yaml.safe_load(fh) or {}
            elif suffix == ".json":
                with open(path, "r", encoding="utf-8") as fh:
                    self._raw = json.load(fh) or {}
        except Exception as e:
            print(f"❌ 加载配置文件失败: {path}")
            print(f"❌ 错误信息: {e}")

    def _find_file(self) -> Optional[Path]:
        for d in _CONFIG_DIRS:
            for f in _CONFIG_FILES:
                path = Path(d, f)
                if path.exists():
                    return path
        return None

    # ---- Section 访问 ----

    def section(self, name: str) -> dict[str, Any]:
        """获取整个配置段 (如 database / logging / celery)"""
        self._ensure_loaded()
        sec = self._raw.get(name, {})
        return sec if isinstance(sec, dict) else {}

    # ---- 取值 (env 优先) ----

    def get(
        self,
        section: str,
        key: str,
        env: str = None,
        default: Any = None,
    ) -> Any:
        """取值: 环境变量 > 配置文件 > 默认值"""
        # 1) 环境变量
        if env:
            val = os.getenv(env)
            if val is not None:
                return self._cast(val, default)
        # 2) 配置文件
        self._ensure_loaded()
        sec = self._raw.get(section)
        if isinstance(sec, dict) and key in sec:
            return sec[key]
        return default

    def get_int(
        self,
        section: str,
        key: str,
        env: str = None,
        default: int = 0,
    ) -> int:
        val = self.get(section, key, env=env, default=default)
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def get_bool(
        self,
        section: str,
        key: str,
        env: str = None,
        default: bool = False,
    ) -> bool:
        val = self.get(section, key, env=env, default=default)
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("1", "true", "yes")

    def get_list(
        self,
        section: str,
        key: str,
        env: str = None,
        default: list = None,
    ) -> list:
        """取列表 (env 支持逗号分隔)"""
        if default is None:
            default = []
        val = self.get(section, key, env=env)
        if val is None:
            return default
        if isinstance(val, list):
            return val
        # env 字符串 → 列表 (逗号分隔)
        return [v.strip() for v in str(val).split(",") if v.strip()]

    def get_section_or_env(
        self,
        section: str,
        env_prefix: str = None,
    ) -> dict[str, Any]:
        """获取整个 section, 并叠加环境变量

        环境变量命名: {env_prefix}_{KEY} → key 小写
        例: MONGODB_HOST → section 中 host 字段被覆盖
        """
        sec = dict(self.section(section))
        if env_prefix:
            prefix = env_prefix.rstrip("_") + "_"
            for env_key, env_val in os.environ.items():
                if env_key.startswith(prefix):
                    cfg_key = env_key[len(prefix):].lower()
                    sec[cfg_key] = self._cast(env_val, sec.get(cfg_key))
        return sec

    # ---- 内部 ----

    @staticmethod
    def _cast(value: str, default: Any) -> Any:
        """类型推断"""
        if isinstance(default, bool):
            return value.strip().lower() in ("1", "true", "yes")
        if isinstance(default, int):
            try:
                return int(value)
            except ValueError:
                return value
        if isinstance(default, float):
            try:
                return float(value)
            except ValueError:
                return value
        if isinstance(default, list):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value


# 全局单例
config = ConfigLoader()
