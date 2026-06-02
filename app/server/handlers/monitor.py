"""
监控数据接口

URL:
    POST   /api/monitor         新增基金
    GET    /api/monitor         查询全部基金
    GET    /api/monitor/{id}    查询指定基金
    PUT    /api/monitor/{id}    全量替换基金
    DELETE /api/monitor/{id}    删除基金
    PATCH  /api/monitor/{id}    部分更新基金
"""

from app.server.handlers._base import BaseHandler


class MonitorHandler(BaseHandler):
    NAME = "monitor"
    DB = "fly_python"
    COLLECTION = "monitor"

    # 所有 CRUD 方法继承自 BaseHandler, 无需重复编写
    # 如果需要自定义逻辑, 直接重写对应方法即可