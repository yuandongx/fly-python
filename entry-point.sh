#!/bin/bash
# ============================================
# Fly-Python 容器入口脚本
# 用法:
#   entry-point.sh              → 默认启动 bash
#   entry-point.sh server       → 启动 FastAPI 服务
#   entry-point.sh worker       → 启动 Celery Worker
#   entry-point.sh beat         → 启动 Celery Beat (定时调度)
#   entry-point.sh all          → 同时启动 Worker + Beat
# ============================================

set -e

cd /app

case "${1:-bash}" in

    server)
        echo "[entry] 启动 FastAPI 服务..."
        exec python main.py
        ;;

    worker)
        echo "[entry] 启动 Celery Worker..."
        exec celery -A celery_app worker --loglevel=info
        ;;

    beat)
        echo "[entry] 启动 Celery Beat..."
        exec celery -A celery_app beat --loglevel=info
        ;;

    all)
        echo "[entry] 启动 Celery Worker + Beat..."
        exec celery -A celery_app worker --beat --loglevel=info
        ;;

    bash|sh)
        exec /bin/bash
        ;;

    *)
        # 允许直接传任意命令
        exec "$@"
        ;;

esac
