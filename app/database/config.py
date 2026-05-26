"""
数据库配置管理 (委托给 app.load_config)
优先级: 环境变量 > YAML 配置文件 > 默认值
"""
from app.load_config import config as _global_config


class _Config:
    """数据库配置适配层, 保持原有调用接口不变"""

    def get(self, key: str, default=None):
        return _global_config.get("database", key, default=default)

    def get_int(self, key: str, default: int = 0) -> int:
        return _global_config.get_int("database", key, default=default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        return _global_config.get_bool("database", key, default=default)


# 全局单例 (保持原有导出)
config = _Config()
