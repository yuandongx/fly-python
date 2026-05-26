"""
Handler 基类

- 每个业务模块继承 BaseHandler 并覆盖 NAME / DB / COLLECTION
- NAME 自动映射为 URL 前缀: /api/{NAME}
- DB / COLLECTION 自动绑定数据库 CRUD 实例
- 可选择性重写 post / get / put / delete / patch 方法

子类示例:

    from app.server.handlers._base import BaseHandler

    class UserHandler(BaseHandler):
        NAME = "user"
        DB = "fly_python"
        COLLECTION = "users"

        def get(self, item_id: str = None):
            if item_id:
                return self.crud.find_one({"_id": item_id})
            return self.crud.find_many()

        def post(self, data: dict):
            return self.crud.insert_one(data)

        def delete(self, item_id: str):
            return self.crud.delete_one({"_id": item_id})
"""

from typing import Any

from app.database import CRUD, get_crud


class BaseHandler:
    """通用 Handler 基类 — 每个子类 = 一组 RESTful 接口"""

    # ---- 子类必须/应该重写的属性 ----
    NAME: str = None           # URL 前缀, 如 "user" → /api/user
    DB: str = "fly_python"    # MongoDB 数据库名
    COLLECTION: str = "base"   # MongoDB 集合名

    # ---- 内部能力 ----

    @property
    def crud(self) -> CRUD:
        """懒加载: 首次访问时绑定数据库集合"""
        if getattr(self, "_crud", None) is None:
            self._crud = get_crud(self.COLLECTION, self.DB)
        return self._crud

    # ======================== RESTful 端点 ========================

    def post(self, data: dict) -> Any:
        """新增 — POST /api/{NAME}"""
        result = self.crud.insert_one(data)
        return {"id": str(result.inserted_id)}

    def get(self, item_id: str = None) -> Any:
        """查询 — GET /api/{NAME}[/{item_id}]"""
        if item_id:
            doc = self.crud.find_one({"_id": item_id})
            if doc is None:
                return {"error": "not found"}
            return doc
        return self.crud.find_many()

    def put(self, item_id: str, data: dict) -> Any:
        """全量更新 — PUT /api/{NAME}/{item_id}"""
        result = self.crud.replace_one({"_id": item_id}, data, upsert=False)
        if result.matched_count == 0:
            return {"error": "not found"}
        return {"updated": True}

    def delete(self, item_id: str) -> Any:
        """删除 — DELETE /api/{NAME}/{item_id}"""
        result = self.crud.delete_one({"_id": item_id})
        if result.deleted_count == 0:
            return {"error": "not found"}
        return {"deleted": True}

    def patch(self, item_id: str, data: dict) -> Any:
        """部分更新 — PATCH /api/{NAME}/{item_id}"""
        result = self.crud.update_one(
            {"_id": item_id},
            {"$set": data},
            upsert=False,
        )
        if result.matched_count == 0:
            return {"error": "not found"}
        return {"updated": True}
