"""
handlers 包 — 所有业务接口放在此目录

新增接口只需:
    1. 新建一个 .py 文件
    2. 继承 BaseHandler, 设置 NAME / DB / COLLECTION
    3. server/__init__.py 会自动发现并注册路由

示例见 user.py
"""
