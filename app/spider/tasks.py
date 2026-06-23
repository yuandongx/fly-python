"""
Celery 任务定义

- 异步任务: 直接 @app.task 装饰
- 定时任务: 在 config.yml → celery.beat_schedule 中配置 crontab

用法:
    from app.spider.tasks import scrape_page, batch_scrape

    # 异步调用 (立即返回 AsyncResult)
    result = scrape_page.delay("https://example.com/page/1")

    # 获取结果
    if result.ready():
        data = result.get()
"""

import time
from typing import Any, Optional

from celery import group, chain, chord
from celery.utils.log import get_task_logger

from celery_app import app
from app.database import get_crud

logger = get_task_logger(__name__)


def _t() -> str:
    """返回当前时间的字符串表示"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# ============================
# 异步任务 sina
# ============================
@app.task(bind=True, max_retries=3, default_retry_delay=60, name="app.spider.tasks.task_get_sina_data")
def task_get_sina_data(self) -> dict:
    from app.spider.fetch.sina import get_sina_data
    task_name = "app.spider.tasks.task_get_sina_data"
    task_curd = get_crud("spider_task")
    start_time = _t()
    task_curd.insert_one({
        "task": task_name,
        "status": "started",
        "start_time": start_time
    })
    try:
        data = get_sina_data()
        crud = get_crud("stock")
        crud.update_many(key="symbol", many=data, upsert=True)
        logger.info("成功获取新浪数据: %d 条记录", len(data))
        task_curd.update_one({"task": task_name, "start_time": start_time},
                              {"$set": {"status": "completed", "end_time": _t()}})
        return {"status": "success", "count": len(data)}
    except Exception as exc:
        logger.error("获取新浪数据失败: %s", exc)
        crud = get_crud("spider_results")
        crud.insert_one({
            "status": "error",
            "error": str(exc),
            "time": _t()
        })
        task_curd.update_one({"task": task_name, "start_time": start_time},
                              {"$set": {"status": "failed", "end_time": _t()}})
# ===========================

# 基金排行获取作秀
# get_tiantain_fund_rank_data() --- 直接调用函数获取数据，适合测试和单次执行
# task_get_fund_rank_data() --- 定义为 Celery 任务，适合定时执行或分布式执行
# ============================
@app.task(bind=True, max_retries=3, default_retry_delay=60, name="app.spider.tasks.task_get_fund_rank_data")
def task_get_fund_rank_data(self) -> Optional[dict]:
    """
    获取天天基金排行数据并持久化到数据库
    
    从天天基金网抓取基金排行数据，将结果批量写入 fund 集合，
    同时记录任务执行状态到 spider_task 集合。
    
    Returns:
        Optional[dict]: 执行结果字典，包含以下可能的 status 值：
            - "success": 成功获取并写入数据，附带 count 字段表示记录数
            - "no_data": 未获取到数据
            - "error": 执行异常，附带 message 字段描述错误信息
    """
    from app.spider.fetch.fund_east import get_tiantain_fund_rank_data
    task_curd = get_crud("spider_task") # 任务状态记录
    task_name = "app.spider.tasks.task_get_fund_rank_data"
    start_time = time.time()
    task_curd.insert_one({
        "task": task_name,
        "status": "started",
        "start_time": start_time
    })
    try:
        data = get_tiantain_fund_rank_data()
        rtn = {"status": "success", "count": len(data) if data else 0}
        if data:
            crud = get_crud("fund")
            crud.update_many(key="基金代码", many=data, upsert=True)
            logger.info("成功获取基金排行数据: %d 条记录", len(data))
            rtn = {"status": "success", "count": len(data)}
        else:
            logger.warning("未获取到基金排行数据")
            rtn = {"status": "no_data"}
        task_curd.update_one({"task": task_name, "start_time": start_time},
                              {"$set": {"status": "completed", "end_time": _t()}})
        return rtn
    except Exception as exc:
        logger.error("获取基金排行数据失败: %s", exc)
        crud = get_crud("spider_results")
        crud.insert_one({
            "status": "error",
            "error": str(exc),
            "time": _t()
        })
        task_curd.update_one({"task": task_name, "start_time": start_time},
                              {"$set": {"status": "failed", "end_time": _t()}})
        return {"status": "error", "message": str(exc)}

@app.task(bind=True, max_retries=3, default_retry_delay=60, name="app.spider.tasks.heartbeat")
def heartbeat(self) -> dict:
    """心跳探测 — 用于验证 Celery 链路是否正常"""
    logger.info("心跳任务执行中...")
    return {"status": "alive", "timestamp": _t()}



# ============================
# 定时任务 (在 config.yml 中配置 schedule)
# ============================

@app.task(bind=True, name="app.spider.tasks.cleanup")
def cleanup(self) -> dict:
    """定期清理过期数据 (示例定时任务)"""
    logger.info("定时清理任务开始...")
    crud = get_crud("spider_results")
    cutoff = time.time() - 7 * 24 * 3600  # 7 天前的数据
    crud.delete_many({"ts": {"$lt": cutoff}})
    logger.info("定时清理完成")
    return {"cleaned": "before_7_days"}


@app.task(bind=True, name="app.spider.tasks.daily_report")
def daily_report(self) -> dict:
    """日报统计 (示例定时任务)"""
    logger.info("日报生成中...")
    crud = get_crud("spider_results")
    total = crud.count()
    logger.info("日报: 共 %d 条记录", total)
    return {"total": total, "date": time.strftime("%Y-%m-%d")}
