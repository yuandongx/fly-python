"""
FastAPI 服务入口 — 自动发现并注册 handlers

机制:
    1. 扫描 handlers/ 下所有 handler 模块 (排除 _base 和 __init__)
    2. 对每个 BaseHandler 子类, 根据 NAME 生成 URL: /api/{NAME}
    3. 根据 DB / COLLECTION 自动注入数据库 CRUD
    4. 组装 FastAPI 应用

扩展新接口只需在 handlers/ 下新增文件:

    # handlers/user.py
    from app.server.handlers._base import BaseHandler

    class UserHandler(BaseHandler):
        NAME = "user"
        COLLECTION = "users"
        # 自动获得 get/post/put/delete/patch 能力, 也可重写

用法:
    from app.server import app
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

import importlib
import inspect
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, APIRouter, Path as FastPath, Body, Query, Request
from fastapi.responses import JSONResponse

from app.log_util import logger
from .handlers._base import BaseHandler

_HANDLERS_DIR = Path(__file__).resolve().parent / "handlers"


def not_found_handler():
    return JSONResponse(status_code=404, content={"error": "Not found"})

def _discover_handlers() -> list[type[BaseHandler]]:
    """扫描 handlers/ 目录, 发现所有 BaseHandler 子类"""
    found: list[type[BaseHandler]] = []

    for fpath in _HANDLERS_DIR.glob("*.py"):
        name = fpath.stem
        # 跳过内部模块
        if name.startswith("_") or name == "__init__":
            continue

        try:
            mod = importlib.import_module(f"app.server.handlers.{name}")
        except Exception as exc:
            logger.warning("跳过 handler 模块 %s: %s", name, exc)
            continue

        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (
                inspect.isclass(attr)
                and issubclass(attr, BaseHandler)
                and attr is not BaseHandler
            ):
                found.append(attr)
                logger.info("发现 Handler: %s (NAME=%s, DB=%s, COLLECTION=%s)",
                            attr.__name__, attr.NAME, attr.DB, attr.COLLECTION)

    return found


def _register_handler(app: FastAPI, handler_cls: type[BaseHandler]) -> None:
    """为单个 Handler 类注册 FastAPI 路由"""
    name = handler_cls.NAME
    if not name:
        logger.warning("Handler %s 未设置 NAME, 跳过注册", handler_cls.__name__)
        return

    instance = handler_cls()
    allows = instance.ALLOW_METHOD
    body = instance.BODY_PARAMS
    router = APIRouter(prefix=f"/api/{name}", tags=[name])

    # ------------- POST /api/{name} -------------
    async def _post(request: Request, data = Body(...)):
        try:
            result = instance.post(data, request=request)
            return JSONResponse(content=result)
        except Exception as exc:
            logger.error("POST /api/%s 异常: %s", name, exc)
            return JSONResponse(status_code=500, content={"error": str(exc)})

    if 'POST' in allows:
        router.add_api_route("", _post, methods=["POST"], summary=f"创建 {name}")

    # ------------- GET /api/{name} -------------
    async def _get_list(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(None, ge=1, le=1000, description="每页条数"),
        sort_by: Optional[str] = Query(None, description="排序字段"),
        sort_order: int = Query(-1, ge=-1, le=1, description="排序方向: 1=升序, -1=降序"),
    ):
        try:
            # 收集其他 query 参数作为过滤条件
            filters = {}
            result = instance.get(
                page=page,
                size=size,
                sort_by=sort_by,
                sort_order=sort_order,
                **filters,
            )
            return JSONResponse(content=result)
        except Exception as exc:
            logger.error("GET /api/%s 异常: %s", name, exc)
            return JSONResponse(status_code=500, content={"error": str(exc)})

    if "GET" in allows:
        router.add_api_route("", _get_list, methods=["GET"], summary=f"查询 {name} 列表")

    # ------------- GET /api/{name}/{item_id} -------------
    async def _get_one(item_id: str = FastPath(..., description="文档 ID")):
        try:
            result = instance.get(item_id=item_id)
            if result is None or "error" in result:
                return JSONResponse(status_code=404, content=result)
            return JSONResponse(content=result)
        except Exception as exc:
            logger.error("GET /api/%s/%s 异常: %s", name, item_id, exc)
            return JSONResponse(status_code=500, content={"error": str(exc)})

    router.add_api_route("/{item_id}", _get_one, methods=["GET"], summary=f"查询单个 {name}")

    # ------------- PUT /api/{name}/{item_id} -------------
    async def _put(item_id: str = FastPath(...), data: dict = Body(...)):
        try:
            result = instance.put(item_id, data)
            if "error" in result:
                return JSONResponse(status_code=404, content=result)
            return JSONResponse(content=result)
        except Exception as exc:
            logger.error("PUT /api/%s/%s 异常: %s", name, item_id, exc)
            return JSONResponse(status_code=500, content={"error": str(exc)})

    if "PUT" in allows:
        router.add_api_route("/{item_id}", _put, methods=["PUT"], summary=f"全量更新 {name}")

    # ------------- DELETE /api/{name}/{item_id} -------------
    async def _delete(item_id: str = FastPath(...)):
        try:
            result = instance.delete(item_id)
            if "error" in result:
                return JSONResponse(status_code=404, content=result)
            return JSONResponse(content=result)
        except Exception as exc:
            logger.error("DELETE /api/%s/%s 异常: %s", name, item_id, exc)
            return JSONResponse(status_code=500, content={"error": str(exc)})
    if "DELETE" in allows:
        router.add_api_route("/{item_id}", _delete, methods=["DELETE"], summary=f"删除 {name}")

    # ------------- PATCH /api/{name}/{item_id} -------------
    async def _patch(item_id: str = FastPath(...), data: dict = Body(...)):
        try:
            result = instance.patch(item_id, data)
            if "error" in result:
                return JSONResponse(status_code=404, content=result)
            return JSONResponse(content=result)
        except Exception as exc:
            logger.error("PATCH /api/%s/%s 异常: %s", name, item_id, exc)
            return JSONResponse(status_code=500, content={"error": str(exc)})

    if "PATCH" in allows:
        router.add_api_route("/{item_id}", _patch, methods=["PATCH"], summary=f"部分更新 {name}")

    app.include_router(router)
    logger.info(f"注册路由: /api/{name}/{allows}")


# ---------- 构建 FastAPI 应用 ----------

def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(
        title="Fly Python API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 健康检查
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # 自动发现并注册所有 handler
    handlers = _discover_handlers()
    for h_cls in handlers:
        _register_handler(app, h_cls)

    logger.info("FastAPI 应用初始化完成, 共注册 %d 个 handler", len(handlers))
    return app


# 全局 app 实例
app = create_app()
