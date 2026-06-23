"""配置加载（演示 ConfigMap + 环境变量集成）"""

import os
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """应用配置：从环境变量读取（ConfigMap 注入）"""

    model_config = SettingsConfigDict(env_file=None, case_sensitive=False)

    app_name: str = "k8s-local-stack"
    app_version: str = "v1.0.0"
    log_level: str = "info"
    app_env: str = "development"

    # 模型配置（AMD ROCm 相关）
    model_name: str = "Qwen2.5-7B-Instruct"
    max_workers: int = 4
    enable_metrics: bool = True

    # 服务配置
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # 数据库（演示用，生产从 Secret 注入）
    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "demo"
    db_password: str = "demo123"  # 实际应从 Secret 注入

    # 缓存
    redis_host: str = "redis"
    redis_port: int = 6379


def load_yaml_config() -> dict:
    """从 /etc/config/app.yaml 加载配置（Volume 挂载的 ConfigMap 文件）"""
    config_path = Path("/etc/config/app.yaml")
    if not config_path.exists():
        return {}
    import yaml
    with config_path.open() as f:
        return yaml.safe_load(f) or {}


def get_settings() -> AppSettings:
    """获取应用配置"""
    return AppSettings()