"""
Celery 应用入口
- Broker: Redis (异步任务中间件)
- Backend: MongoDB (任务结果存储)
- 配置: config.yml → 环境变量 → 默认值

启动 Worker:
    celery -A celery_app worker --loglevel=info

启动 Beat (定时任务调度器):
    celery -A celery_app beat --loglevel=info

同时启动 Worker + Beat:
    celery -A celery_app worker --beat --loglevel=info
"""
from celery import Celery
from celery.schedules import crontab

from app.load_config import config


def _parse_beat_schedule(raw: dict) -> dict:
    """将 YAML 中的 beat_schedule 转为 Celery 识别的格式"""
    if not raw:
        return {}
    result = {}
    for name, spec in raw.items():
        if not isinstance(spec, dict):
            continue
        entry = {"task": spec.get("task", "")}
        if "schedule" in spec and isinstance(spec["schedule"], dict):
            entry["schedule"] = crontab(**spec["schedule"])
        elif "schedule" in spec:
            entry["schedule"] = float(spec["schedule"])
        if "args" in spec:
            entry["args"] = spec["args"]
        if "kwargs" in spec:
            entry["kwargs"] = spec["kwargs"]
        result[name] = entry
    return result


# ---------- 创建 Celery 实例 ----------

app = Celery("fly_python")

celery_cfg = config.section("celery")

broker_url = config.get(
    "celery", "broker_url", env="CELERY_BROKER_URL",
    default="redis://127.0.0.1:6379/0",
)
print("====>", broker_url)
result_backend = config.get(
    "celery", "result_backend", env="CELERY_RESULT_BACKEND",
    default="mongodb://127.0.0.1:27017/fly_python",
)

mongo_backend = config.get("celery", "mongodb_backend_settings", default={})
if not isinstance(mongo_backend, dict):
    mongo_backend = {}

app.conf.update(
    # --- Broker ---
    broker_url=broker_url,

    # --- Result Backend (MongoDB) ---
    result_backend=result_backend,
    result_backend_transport_options=mongo_backend,
    result_expires=config.get_int("celery", "result_expires", env="CELERY_RESULT_EXPIRES", default=3600),

    # --- 序列化 ---
    task_serializer=celery_cfg.get("task_serializer", "json"),
    result_serializer=celery_cfg.get("result_serializer", "json"),
    accept_content=list(celery_cfg.get("accept_content", ["json"])),

    # --- 时区 ---
    timezone=config.get("celery", "timezone", env="CELERY_TIMEZONE", default="Asia/Shanghai"),
    enable_utc=bool(celery_cfg.get("enable_utc", False)),

    # --- Worker ---
    worker_concurrency=int(celery_cfg.get("worker_concurrency", 4)),
    worker_prefetch_multiplier=int(celery_cfg.get("worker_prefetch_multiplier", 1)),

    # --- 可靠性 ---
    task_acks_late=bool(celery_cfg.get("task_acks_late", True)),
    task_reject_on_worker_lost=bool(celery_cfg.get("task_reject_on_worker_lost", True)),

    # --- 定时任务 ---
    beat_schedule=_parse_beat_schedule(celery_cfg.get("beat_schedule", {})),

    # --- 自动发现 ---
    imports=["app.spider.tasks"],
)
