# 构建镜像
# 基于官方的python3.14镜像构建
FROM python:3.14

COPY requirements.txt .
# 镜像还能运行nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*;\
    echo "daemon on;" >> /etc/nginx/nginx.conf;\
    pip install -r requirements.txt;

# 设置工作目录
WORKDIR /app
# 复制依赖文件
# 复制应用代码
COPY . .    