"""Day 4 配套 FastAPI 应用

设计要点：
1. /health 返回 200，应用就绪
2. / 返回 pod 标识（演示多副本负载均衡）
3. /version 来自环境变量（演示滚动更新时版本变化）
"""

import os
import socket
from datetime import datetime, timezone

from fastapi import FastAPI, Response

app = FastAPI(title="K8s Deployment Demo")

VERSION = os.getenv("APP_VERSION", "unknown")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")


@app.get("/")
def root():
    return {
        "message": "Hello from K8s Deployment",
        "version": VERSION,
        "hostname": socket.gethostname(),       # 容器主机名
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health():
    """readiness/liveness 探针：永远返回 200"""
    return {"status": "ok", "version": VERSION}


@app.get("/version")
def version():
    return {"version": VERSION, "log_level": LOG_LEVEL}


@app.get("/crash")
def crash():
    """Day 4 实验用：触发进程崩溃，演示 K8s 自愈"""
    import signal
    os.kill(os.getpid(), signal.SIGTERM)