"""
股票数据接口

URL:
    POST   /api/stock         新增股票
    GET    /api/stock         查询全部股票
    GET    /api/stock/{id}    查询指定股票
    PUT    /api/stock/{id}    全量替换股票
    DELETE /api/stock/{id}    删除股票
    PATCH  /api/stock/{id}    部分更新股票
"""

from app.server.handlers._base import BaseHandler


class StockHandler(BaseHandler):
    NAME = "stock"
    DB = "fly_python"
    COLLECTION = "stock"

    # 所有 CRUD 方法继承自 BaseHandler, 无需重复编写
    # 如果需要自定义逻辑, 直接重写对应方法即可