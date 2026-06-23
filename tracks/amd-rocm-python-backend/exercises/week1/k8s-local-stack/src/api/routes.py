"""API 路由"""

import os
import socket
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from .config import get_settings, load_yaml_config

router = APIRouter()
START_TIME = time.time()


@router.get("/")
def root():
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
        "log_level": settings.log_level,
        "model_name": settings.model_name,
        "max_workers": settings.max_workers,
        "hostname": socket.gethostname(),
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/config")
def show_config():
    """展示从 ConfigMap 加载的 YAML 配置"""
    yaml_config = load_yaml_config()
    env_vars = {
        k: v for k, v in os.environ.items()
        if k.startswith(("APP_", "LOG_", "MODEL_", "MAX_", "DB_", "REDIS_"))
    }
    return {
        "yaml_config": yaml_config,
        "env_vars": env_vars,
    }


@router.get("/health")
def health():
    """K8s 健康探针端点"""
    return {"status": "ok"}


@router.get("/ready")
def ready():
    """readiness 探针：可加入 DB/Redis 连通检查"""
    return {"status": "ready"}


@router.get("/crash")
def crash():
    """演示用：触发进程崩溃，验证 K8s 自愈"""
    import signal
    os.kill(os.getpid(), signal.SIGTERM)