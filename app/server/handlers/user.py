"""
用户接口示例

URL:
    POST   /api/user         创建用户
    GET    /api/user         查询全部用户
    GET    /api/user/{id}    查询指定用户
    PUT    /api/user/{id}    全量替换用户
    DELETE /api/user/{id}    删除用户
    PATCH  /api/user/{id}    部分更新用户
"""

from app.server.handlers._base import BaseHandler


class UserHandler(BaseHandler):
    NAME = "user"
    DB = "fly_python"
    COLLECTION = "users"

    # 所有 CRUD 方法继承自 BaseHandler, 无需重复编写
    # 如果需要自定义逻辑, 直接重写对应方法即可:

    # def get(self, item_id: str = None):
    #     """自定义查询: 过滤敏感字段"""
    #     if item_id:
    #         doc = self.crud.find_one({"_id": item_id})
    #         if doc:
    #             doc.pop("password", None)
    #         return doc
    #     docs = self.crud.find_many()
    #     for d in docs:
    #         d.pop("password", None)
    #     return docs
