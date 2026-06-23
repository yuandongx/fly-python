#!/bin/bash

# This script is used to start the application. It sets up the environment and runs the necessary commands to launch the app.

# Usage: ./start.sh

# 目标服务名称
PROJECT_NAME="fly-dev"
TARGET_SERVICE1="test-service"
TARGET_SERVICE2="test-service"

# 检查是否正在运行着目标服务, 如果是, 则停止它们
if pgrep -x "$TARGET_SERVICE1" > /dev/null || pgrep -x "$TARGET_SERVICE2" > /dev/null; then
    echo "Stopping existing services..."
    pkill -f "$TARGET_SERVICE1"
    pkill -f "$TARGET_SERVICE2"
    echo "Existing services stopped."
fi

# 到上一层目录
cd "$(dirname "$0")/.." || exit 1

# 启动目标服务
echo "Starting services..."
# 启动第一个服务
docker-compose -p "$PROJECT_NAME" up -d "$TARGET_SERVICE1"
# 启动第二个服务
docker-compose -p "$PROJECT_NAME" up -d "$TARGET_SERVICE2"
echo "Services started."
