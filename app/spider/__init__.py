"""
app.spider - Celery 异步/定时任务模块

任务存放在 tasks.py 中, 由 celery_app.py 自动发现。

新增任务:
    在 tasks.py 中添加 @app.task 函数即可, 无需额外配置。

定时任务:
    在 config.yml → celery.beat_schedule 中声明 crontab 或间隔。

启动:
    Worker:   celery -A celery_app worker --loglevel=info
    Beat:     celery -A celery_app beat --loglevel=info
    一体化:   celery -A celery_app worker --beat --loglevel=info
"""
