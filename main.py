# Author: xuyuandong
# Date: 2025-12-21 15:12:12
# Description: 主程序

from uvicorn import run
from app.server import create_app

app = create_app()

if __name__ == '__main__':
    run("main:app", host="0.0.0.0", port=8000, reload=True)