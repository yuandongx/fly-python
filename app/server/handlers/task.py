"""
任务数据接口

URL:
    POST   /api/task         新增任务
    GET    /api/task         查询全部任务
    GET    /api/task/{id}    查询指定任务
    PUT    /api/task/{id}    全量替换任务
    DELETE /api/task/{id}    删除任务
    PATCH  /api/task/{id}    部分更新任务
"""

from app.server.handlers._base import BaseHandler


class TaskHandler(BaseHandler):
    NAME = "task"
    DB = "fly_python"
    COLLECTION = "tasks"

    # 所有 CRUD 方法继承自 BaseHandler, 无需重复编写
    # 如果需要自定义逻辑, 直接重写对应方法即可