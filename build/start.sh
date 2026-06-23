#!/bin/bash

# This script is used to start the application. It sets up the environment and runs the necessary commands to launch the app.

# Usage: ./start.sh

# 目标服务名称
PROJECT_NAME="dev"
TARGET_SERVICE1="$PROJECT_NAME"_api_1
TARGET_SERVICE2="$PROJECT_NAME"_worker_1

# 检查是否正在运行着目标服务, 如果是, 则停止它们
docker rm -f $(docker ps -q -f name="$TARGET_SERVICE1")
docker rm -f $(docker ps -q -f name="$TARGET_SERVICE2")
# 到上一层目录
cd "$(dirname "$0")/.." || exit 1
ls -l

# 启动目标服务
echo "Starting services..."
# 启动服务
docker-compose -p "$PROJECT_NAME" -f build/docker-compose-api.yml up -d 
