"""Day 5 配套：演示 Service 负载均衡的 FastAPI 应用

每次 GET / 都会返回容器 hostname，验证 Service 流量分发到不同 Pod
"""

import os
import socket
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request

app = FastAPI(title="K8s Service Demo")

START_TIME = time.time()


@app.get("/")
def root(request: Request):
    return {
        "message": "Hello via K8s Service",
        "version": os.getenv("APP_VERSION", "unknown"),
        "hostname": socket.gethostname(),
        "client_ip": request.client.host if request.client else "unknown",
        "time": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    """展示 Pod 详细信息"""
    return {
        "hostname": socket.gethostname(),
        "pod_ip": os.getenv("POD_IP", "unknown"),
        "node_name": os.getenv("NODE_NAME", "unknown"),
        "version": os.getenv("APP_VERSION", "unknown"),
        "env": os.getenv("APP_ENV", "unknown"),
    }