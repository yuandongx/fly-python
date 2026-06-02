"""
监控数据接口

URL:
    POST   /api/follow         新增关注
    GET    /api/follow         查询全部关注
    GET    /api/follow/{id}    查询指定关注
    PUT    /api/follow/{id}    全量替换关注
    DELETE /api/follow/{id}    删除关注
    PATCH  /api/follow/{id}    部分更新关注
"""

from app.server.handlers._base import BaseHandler


class FollowHandler(BaseHandler):
    NAME = "follow"
    DB = "fly_python"
    COLLECTION = "follows"

    # 所有 CRUD 方法继承自 BaseHandler, 无需重复编写
    # 如果需要自定义逻辑, 直接重写对应方法即可