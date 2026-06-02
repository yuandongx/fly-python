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
    NAME: str = None            # URL 前缀, 如 "user" → /api/user
    DB: str = "fly_python"      # MongoDB 数据库名
    COLLECTION: str = "base"    # MongoDB 集合名
    PAGE_SIZE: int = 20         # 默认分页大小

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

    def get(
        self,
        item_id: str = None,
        page: int = 1,
        size: int = None,
        sort_by: str = None,
        sort_order: int = -1,
        **filters,
    ) -> Any:
        """查询 — GET /api/{NAME}[/{item_id}]

        列表查询支持:
          - 分页:  page / size
          - 排序:  sort_by / sort_order (1=升序, -1=降序)
          - 过滤:  其余 query 参数自动作为等于过滤条件
        """
        if item_id:
            doc = self.crud.find_one({"_id": item_id})
            if doc is None:
                return {"error": "not found"}
            doc["id"] = str(doc.pop("_id"))
            return doc

        # ---- 列表查询: 分页 + 过滤 + 排序 ----
        size = size or self.PAGE_SIZE
        skip = max(0, (page - 1)) * size

        # 构建排序
        sort = None
        if sort_by:
            sort = [(sort_by, sort_order)]

        # 总数
        total = self.crud.count(filters)

        # 查询数据
        items = self.crud.find_many(
            filter_dict=filters,
            sort=sort,
            skip=skip,
            limit=size,
        )

        # 将ObjectId 转为字符串, 以便 JSON 序列化
        for item in items:
            item["id"] = str(item.pop("_id"))

        return {
            "total": total,
            "page": page,
            "size": size,
            "pages": max(1, (total + size - 1) // size) if total else 1,
            "items": items,
        }

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
        # update_one 内部已做 {"$set": data} 包装, 此处直接传 data 即可
        result = self.crud.update_one(
            {"_id": item_id},
            data,
            upsert=False,
        )
        if result.matched_count == 0:
            return {"error": "not found"}
        return {"updated": True}
