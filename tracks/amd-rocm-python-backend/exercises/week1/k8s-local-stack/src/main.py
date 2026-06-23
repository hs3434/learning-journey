"""FastAPI 入口"""

import logging
import os

from fastapi import FastAPI

from .api.routes import router

# 配置日志
log_level = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="k8s-local-stack",
    version=os.getenv("APP_VERSION", "0.1.0"),
    description="基于 Kubernetes 的 Python Web 应用完整部署示例",
)
app.include_router(router)


@app.on_event("startup")
async def startup():
    logger.info("=" * 50)
    logger.info("k8s-local-stack starting up")
    logger.info(f"  Version: {os.getenv('APP_VERSION', 'unknown')}")
    logger.info(f"  Env:     {os.getenv('APP_ENV', 'unknown')}")
    logger.info(f"  Model:   {os.getenv('MODEL_NAME', 'unknown')}")
    logger.info("=" * 50)