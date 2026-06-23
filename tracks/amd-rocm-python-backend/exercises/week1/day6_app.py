"""Day 6 配套：演示 ConfigMap + Secret 注入的 FastAPI 应用

关键点：
1. 从环境变量读取 ConfigMap
2. 从 /etc/config/app.yaml 读取挂载的配置文件
3. 从 /etc/secret/ 读取 base64 编码的 Secret
4. 演示 Secret 解码（生产中密码应该来自 secret store，不应解到日志）
"""

import os
import base64
import logging
import socket
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=os.getenv("LOG_LEVEL", "info").upper())
logger = logging.getLogger(__name__)

app = FastAPI(title="K8s ConfigMap & Secret Demo")


# ---- 启动时加载配置 ----
@app.on_event("startup")
def startup():
    """演示从 ConfigMap 挂载的文件加载 YAML 配置"""
    global app_settings
    config_file = Path("/etc/config/app.yaml")
    if config_file.exists():
        with config_file.open() as f:
            app_settings = yaml.safe_load(f)
        logger.info(f"Loaded config: {app_settings}")
    else:
        app_settings = {}
        logger.warning("No config file found at /etc/config/app.yaml")


# ---- 路由 ----
@app.get("/")
def root():
    return {
        "app_name": os.getenv("APP_NAME", "unknown"),
        "version": os.getenv("APP_VERSION", "unknown"),
        "log_level": os.getenv("LOG_LEVEL", "unknown"),
        "app_env": os.getenv("APP_ENV", "unknown"),
        "model_name": os.getenv("MODEL_NAME", "unknown"),
        "max_workers": os.getenv("MAX_WORKERS", "unknown"),
        "hostname": socket.gethostname(),
    }


@app.get("/config")
def show_config():
    """展示从 /etc/config/app.yaml 加载的配置"""
    return app_settings


@app.get("/secret-status")
def secret_status():
    """演示：从 /etc/secret 读取 Secret（不返回明文）"""
    secret_dir = Path("/etc/secret")
    if not secret_dir.exists():
        raise HTTPException(status_code=404, detail="no secret dir")

    files = {}
    for f in secret_dir.iterdir():
        # ⚠️ 生产中应避免返回敏感内容，这里只返回文件名 + 是否存在
        files[f.name] = {
            "size": f.stat().st_size,
            "exists": True,
        }
    return {"secret_files": files}


@app.get("/secret-decode")
def secret_decode():
    """演示：解码 base64 后的 Secret（仅用于教学，生产应避免）"""
    password_file = Path("/etc/secret/password")
    if not password_file.exists():
        raise HTTPException(status_code=404, detail="no password file")
    encoded = password_file.read_text().strip()
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"decode failed: {e}")
    return {"encoded": encoded, "decoded": decoded}


@app.get("/health")
def health():
    return {"status": "ok"}