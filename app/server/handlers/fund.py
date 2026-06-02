"""
基金数据接口

URL:
    POST   /api/fund         新增基金
    GET    /api/fund         查询全部基金
    GET    /api/fund/{id}    查询指定基金
    PUT    /api/fund/{id}    全量替换基金
    DELETE /api/fund/{id}    删除基金
    PATCH  /api/fund/{id}    部分更新基金
"""

from app.server.handlers._base import BaseHandler


class FundHandler(BaseHandler):
    NAME = "fund"
    DB = "fly_python"
    COLLECTION = "funds"

    # 所有 CRUD 方法继承自 BaseHandler, 无需重复编写
    # 如果需要自定义逻辑, 直接重写对应方法即可