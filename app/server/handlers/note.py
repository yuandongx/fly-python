"""
监控数据接口

URL:
    POST   /api/note         新增笔记
    GET    /api/note         查询全部笔记
    GET    /api/note/{id}    查询指定笔记
    PUT    /api/note/{id}    全量替换笔记
    DELETE /api/note/{id}    删除笔记
    PATCH  /api/note/{id}    部分更新笔记
"""

from app.server.handlers._base import BaseHandler


class noteHandler(BaseHandler):
    NAME = "note"
    DB = "fly_python"
    COLLECTION = "notes"

    # 所有 CRUD 方法继承自 BaseHandler, 无需重复编写
    # 如果需要自定义逻辑, 直接重写对应方法即可