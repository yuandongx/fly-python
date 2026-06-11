# 构建镜像
# 基于官方的python3.14镜像构建
FROM python:3.14

COPY . /app
# 镜像还能运行nginx
RUN pip install -r /app/requirements.txt

# 设置工作目录
WORKDIR /app

ENTRYPOINT ["/app/entry-point.sh"]