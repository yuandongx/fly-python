"""
app.database - 数据库模块

用法:
    from app.database import get_crud

    crud = get_crud("users")
    crud.insert_one({"name": "test", "age": 25})
    results = crud.find_many({"age": {"$gte": 18}}, limit=10)

    # 使用 MongoQuery 链式查询
    from app.database import MongoQuery
    q = MongoQuery().age >= 18
    q.field("status")._in(["active", "pending"])
    results = crud.find_many(q.build())
"""
from .connection import connection, ConnectionManager
from .crud import CRUD, MongoQuery
from .config import config


def get_crud(collection: str, db_name: str = None) -> CRUD:
    """快捷获取指定集合的 CRUD 实例"""
    return CRUD(connection.get_collection(collection, db_name))


def get_database(db_name: str = None):
    """获取数据库实例 (兼容更高级操作)"""
    return connection.get_database(db_name)


def close():
    """关闭数据库连接池"""
    connection.close()


__all__ = [
    "connection",
    "ConnectionManager",
    "CRUD",
    "MongoQuery",
    "config",
    "get_crud",
    "get_database",
    "close",
]
