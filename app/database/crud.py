"""
通用 CRUD 操作 (基于 MongoDB)

支持的查询风格:
- 直接传 dict 作为 filter
- 高级: MongoQuery 对象支持 gt/gte/lt/lte/in/nin/ne/exists/regex
"""
from typing import Any, Optional

from pymongo.collection import Collection
from pymongo import UpdateOne
from pymongo.results import InsertOneResult, InsertManyResult, DeleteResult, UpdateResult

# 导出
__all__ = [
    "CRUD",
    "MongoQuery",
]


# ---------- 查询构建器 ----------

class _Operator:
    def __init__(self, field: str, parent: "MongoQuery"):
        self._field = field
        self._parent = parent

    def __eq__(self, value):
        self._parent._filters[self._field] = value
        return self._parent

    def __gt__(self, value):
        self._parent._filters[self._field] = {"$gt": value}
        return self._parent

    def __ge__(self, value):
        self._parent._filters[self._field] = {"$gte": value}
        return self._parent

    def __lt__(self, value):
        self._parent._filters[self._field] = {"$lt": value}
        return self._parent

    def __le__(self, value):
        self._parent._filters[self._field] = {"$lte": value}
        return self._parent

    def __ne__(self, value):
        self._parent._filters[self._field] = {"$ne": value}
        return self._parent


class MongoQuery:
    """链式查询构建器

    用法:
        q = MongoQuery().name == "foo"
        q = q.age >= 18
        q = q.status._in(["active", "pending"])
        q = q.email._regex(r"@gmail\.com$")
        filter_dict = q.build()
    """

    def __init__(self):
        self._filters: dict = {}

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return _Operator(name, self)

    # ---- 特殊方法挂在 _Operator 上不现实，提供独立方法 ----

    def field(self, name: str) -> "_FieldOps":
        """显式获取字段操作对象 (支持 in/nin/exists/regex)"""
        return _FieldOps(name, self)

    def build(self) -> dict:
        return dict(self._filters)


class _FieldOps:
    """字段级高级操作"""

    def __init__(self, field: str, query: MongoQuery):
        self._field = field
        self._query = query

    def _in(self, values: list) -> MongoQuery:
        self._query._filters[self._field] = {"$in": values}
        return self._query

    def _nin(self, values: list) -> MongoQuery:
        self._query._filters[self._field] = {"$nin": values}
        return self._query

    def _exists(self, value: bool = True) -> MongoQuery:
        self._query._filters[self._field] = {"$exists": value}
        return self._query

    def _regex(self, pattern: str, options: str = "") -> MongoQuery:
        self._query._filters[self._field] = {"$regex": pattern, "$options": options}
        return self._query


# ---------- CRUD 基类 ----------

class CRUD:
    """通用单条 / 批量 CRUD"""

    def __init__(self, collection: Collection):
        self._col = collection

    @property
    def collection(self) -> Collection:
        return self._col

    # ======================== 新增 ========================

    def insert_one(self, document: dict) -> InsertOneResult:
        """插入单条文档"""
        return self._col.insert_one(document)

    def insert_many(self, documents: list[dict]) -> InsertManyResult:
        """批量插入文档"""
        return self._col.insert_many(documents)

    # ======================== 查询 ========================

    def find_one(self, filter_dict: dict = None, **kwargs) -> Optional[dict]:
        """查询单条"""
        filter_dict = filter_dict or {}
        return self._col.find_one(filter_dict, **kwargs)

    def find_many(
        self,
        filter_dict: dict = None,
        sort: list[tuple[str, int]] = None,
        skip: int = 0,
        limit: int = 0,
        **kwargs,
    ) -> list[dict]:
        """查询多条 (带分页/排序)"""
        filter_dict = filter_dict or {}
        cursor = self._col.find(filter_dict, **kwargs)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def count(self, filter_dict: dict = None) -> int:
        """统计数量"""
        return self._col.count_documents(filter_dict or {})

    # ======================== 更新 ========================

    def update_one(
        self,
        filter_dict: dict,
        data: dict,
        upsert: bool = False,
    ) -> UpdateResult:
        """更新单条"""
        return self._col.update_one(filter_dict, data, upsert=upsert)

    def update_many(
        self,
        key: str,
        many: list[Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """批量更新,批量写入数据
        """
        updates = []
        for one in many:
            if key in one:
                updates.append(UpdateOne({key: one[key]}, {"$set": one}, upsert=upsert))
        if not updates:
            return UpdateResult({"n": 0, "nModified": 0, "upserted": []}, acknowledged=True)
        return self._col.bulk_write(updates)

    def replace_one(
        self,
        filter_dict: dict,
        replacement: dict,
        upsert: bool = False,
    ) -> UpdateResult:
        """替换单条文档 (整个文档替换)"""
        return self._col.replace_one(filter_dict, replacement, upsert=upsert)

    # ======================== 删除 ========================

    def delete_one(self, filter_dict: dict) -> DeleteResult:
        """删除单条"""
        return self._col.delete_one(filter_dict)

    def delete_many(self, filter_dict: dict) -> DeleteResult:
        """批量删除"""
        return self._col.delete_many(filter_dict)

    # ======================== 聚合 ========================

    def aggregate(self, pipeline: list[dict]) -> list[dict]:
        """聚合管道"""
        return list(self._col.aggregate(pipeline))
