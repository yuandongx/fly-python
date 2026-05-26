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


# ============================
# 异步任务 sina
# ============================
@app.task(bind=True, max_retries=3, default_retry_delay=60, name="app.spider.tasks.task_get_sina_data")
def task_get_sina_data(self) -> dict:
    from app.spider.fetch.sina import get_sina_data
    task_name = "app.spider.tasks.task_get_sina_data"
    task_curd = get_crud("spider_task")
    start_time = time.time()
    task_curd.insert_one({
        "task": task_name,
        "status": "started",
        "start_time": start_time
    })
    try:
        data = get_sina_data()
        crud = get_crud("stock")
        crud.update_many(key="idx", many=data, upsert=True)
        logger.info("成功获取新浪数据: %d 条记录", len(data))
        task_curd.update_one({"task": task_name, "start_time": start_time},
                              {"$set": {"status": "completed", "end_time": time.time()}})
        return {"status": "success", "count": len(data)}
    except Exception as exc:
        logger.error("获取新浪数据失败: %s", exc)
        crud = get_crud("spider_results")
        crud.insert_one({
            "status": "error",
            "error": str(exc),
            "ts": time.time()
        })
        task_curd.update_one({"task": task_name, "start_time": start_time},
                              {"$set": {"status": "failed", "end_time": time.time()}})

@app.task(bind=True, max_retries=3, default_retry_delay=60, name="app.spider.tasks.heartbeat")
def heartbeat(self) -> dict:
    """心跳探测 — 用于验证 Celery 链路是否正常"""
    logger.info("心跳任务执行中...")
    return {"status": "alive", "timestamp": time.time()}


@app.task(bind=True, max_retries=3, time_limit=300, name="app.spider.tasks.scrape_page")
def scrape_page(self, url: str, meta: dict = None) -> dict:
    """抓取单个页面 — 异步执行, 结果存入 MongoDB"""
    logger.info("开始抓取: %s", url)
    try:
        # ---- 实际抓取逻辑 (替换为你的实现) ----
        import requests
        resp = requests.get(url, timeout=30)
        data = {
            "url": url,
            "status": resp.status_code,
            "size": len(resp.text),
            "ts": time.time(),
        }
        # ---- 结果持久化到 MongoDB ----
        crud = get_crud("spider_results")
        crud.insert_one(data)
        logger.info("抓取完成: %s → %d 字节", url, data["size"])
        return data
    except Exception as exc:
        logger.error("抓取失败 %s: %s", url, exc)
        raise self.retry(exc=exc)


@app.task(bind=True, name="app.spider.tasks.batch_scrape")
def batch_scrape(self, urls: list[str]) -> list[dict]:
    """批量抓取 — 内部通过 Celery group 并发执行"""
    logger.info("批量抓取 %d 个页面", len(urls))
    job = group(scrape_page.s(url) for url in urls)
    result = job.apply_async()
    results = result.join()  # 等待全部完成
    return results


@app.task(bind=True, name="app.spider.tasks.parse_data")
def parse_data(self, raw_data: dict) -> dict:
    """示例后处理任务 (可用于 chain/chord 编排)"""
    logger.info("后处理数据: %s", raw_data.get("url", ""))
    time.sleep(0.1)  # 模拟耗时
    return {"parsed": True, "source": raw_data.get("url", "")}


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
