# ---- 阶段 1：构建 wheel ----
FROM python:3.11-slim AS builder

WORKDIR /app

# 装构建依赖（仅 builder 阶段需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.30" \
    "pydantic>=2.9" \
    "pydantic-settings>=2.5" \
    "pyyaml>=6.0"

# ---- 阶段 2：运行时 ----
FROM python:3.11-slim AS runtime

# 安全：创建非 root 用户
RUN groupadd -r app && useradd -r -g app --home /app app

WORKDIR /app

# 从 builder 拷贝 wheel 并安装
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels \
        fastapi uvicorn pydantic pydantic-settings pyyaml \
    && rm -rf /wheels

# 拷贝应用代码
COPY --chown=app:app src/ ./src/

USER app
EXPOSE 8000

# 健康检查（容器层面，K8s 探针是更细粒度的）
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]