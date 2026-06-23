"""Day 2 配套的 FastAPI 应用

演示与 Redis / PostgreSQL 的连通性，验证 docker-compose 网络配置。
"""

import os
import logging

import redis
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=os.getenv("LOG_LEVEL", "info"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Docker Compose Demo", version="0.1.0")


class Item(BaseModel):
    key: str
    value: str


# 启动时建立连接
@app.on_event("startup")
def startup():
    """初始化连接池"""
    global redis_client, pg_conn
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
    )
    pg_conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        user=os.getenv("POSTGRES_USER", "demo"),
        password=os.getenv("POSTGRES_PASSWORD", "demo123"),
        dbname=os.getenv("POSTGRES_DB", "demo"),
    )
    # 创建测试表
    with pg_conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT
            )
        """)
    pg_conn.commit()
    logger.info("✓ Connected to Redis & PostgreSQL")


@app.get("/")
def root():
    return {
        "message": "Hello from Docker Compose",
        "env": os.getenv("APP_ENV", "unknown"),
        "hostname": os.uname().nodename,
    }


@app.get("/health")
def health():
    """健康检查：同时验证 redis 和 pg 连通"""
    status = {"app": "ok", "redis": "unknown", "postgres": "unknown"}
    try:
        status["redis"] = "ok" if redis_client.ping() else "fail"
    except Exception as e:
        status["redis"] = f"fail: {e}"
    try:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT 1")
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"fail: {e}"
    return status


@app.get("/redis-test")
def redis_test():
    """Redis 连通测试"""
    redis_client.set("test_key", "hello", ex=60)
    value = redis_client.get("test_key")
    return {"redis_value": value}


@app.get("/db-test")
def db_test():
    """PostgreSQL 连通测试"""
    with pg_conn.cursor() as cur:
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
    return {"postgres_version": version}


@app.post("/items")
def create_item(item: Item):
    """写入 redis + pg（演示双写）"""
    redis_client.set(f"item:{item.key}", item.value, ex=300)
    with pg_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO items (key, value) VALUES (%s, %s) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            (item.key, item.value),
        )
    pg_conn.commit()
    return {"key": item.key, "value": item.value}


@app.get("/items/{key}")
def read_item(key: str):
    """先查 redis 缓存，再查 pg"""
    cached = redis_client.get(f"item:{key}")
    if cached:
        return {"source": "cache", "value": cached}
    with pg_conn.cursor() as cur:
        cur.execute("SELECT value FROM items WHERE key = %s", (key,))
        row = cur.fetchone()
    if row:
        redis_client.set(f"item:{key}", row[0], ex=300)
        return {"source": "db", "value": row[0]}
    return {"error": "not found"}