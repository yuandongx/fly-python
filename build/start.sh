#!/bin/bash

# This script is used to start the application. It sets up the environment and runs the necessary commands to launch the app.

# Usage: ./start.sh

# 目标服务名称
PROJECT_NAME="dev"
TARGET_SERVICE1="$PROJECT_NAME\_api_1"
TARGET_SERVICE2="$PROJECT_NAME\_worker_1"

# 检查是否正在运行着目标服务, 如果是, 则停止它们
docker ps -q -f name="$TARGET_SERVICE1" | grep -q . && {
    echo "Stopping existing service: $TARGET_SERVICE1"
    docker-compose -p "$PROJECT_NAME" stop "$TARGET_SERVICE1"
}
docker ps -q -f name="$TARGET_SERVICE2" | grep -q . && {
    echo "Stopping existing service: $TARGET_SERVICE2"
    docker-compose -p "$PROJECT_NAME" stop "$TARGET_SERVICE2"
}

# 到上一层目录
cd "$(dirname "$0")/.." || exit 1

# 启动目标服务
echo "Starting services..."
# 启动第一个服务
docker-compose -p "$PROJECT_NAME" up -d "$TARGET_SERVICE1"
# 启动第二个服务
docker-compose -p "$PROJECT_NAME" up -d "$TARGET_SERVICE2"
echo "Services started."
