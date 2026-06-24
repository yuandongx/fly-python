"""
用户接口示例

URL:
    POST   /api/zs         创建指数
    GET    /api/zs         查询指数
    GET    /api/zs/{id}    查询指定指数
    PUT    /api/zs/{id}    全量替换指数
    DELETE /api/zs/{id}    删除指数
    PATCH  /api/zs/{id}    部分更新指数
"""

from app.server.handlers._base import BaseHandler


class ZsHandler(BaseHandler):
    NAME = "zs"
    # DB = "fly_python"
    COLLECTION = "zs"

    # 所有 CRUD 方法继承自 BaseHandler, 无需重复编写
    # 如果需要自定义逻辑, 直接重写对应方法即可: