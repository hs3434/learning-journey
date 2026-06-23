# Day 1: Docker 多阶段构建与镜像优化

## 1. 为什么需要多阶段构建？

单阶段构建的痛点：
- 镜像包含构建工具（gcc、make、dev headers），体积膨胀
- 源码、测试代码、`.git` 被打进镜像，**安全风险**
- 部署到 K8s 后拉镜像慢、冷启动慢

多阶段构建的核心思想：**一个 Dockerfile 多阶段**，只在最终阶段保留运行时必需的文件。

## 2. 镜像分层与缓存机制

Dockerfile 每一行 = 一个 layer（只读文件系统层）。规则：
- 变更频繁的层放**后面**
- 不变的层放**前面**并利用缓存

```dockerfile
# ❌ 反例：requirements 变更导致整个 pip install 重跑
COPY . /app
RUN pip install -r requirements.txt

# ✅ 正例：依赖先装，代码后拷
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
```

## 3. 基础镜像选择

| 镜像 | 大小 | 兼容性 | 适用 |
|------|------|--------|------|
| `python:3.11` | ~900MB | 全 | 不推荐用于生产 |
| `python:3.11-slim` | ~150MB | glibc 兼容 | **推荐**（Debian 基础）|
| `python:3.11-alpine` | ~50MB | musl libc，部分 wheel 不兼容 | 谨慎使用 |
| `python:3.11-slim-bookworm` | ~150MB | 显式 Debian 版本 | 生产推荐 |

> **本项目统一用 `python:3.11-slim`**，AMD ROCm 镜像层也基于此。

## 4. `.dockerignore` 必备

```
.git
.gitignore
.venv
venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
*.md
tests
```

## 5. 多阶段构建实战

### 单阶段（不推荐）

```dockerfile
# stage1/Dockerfile.single
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 多阶段（推荐）

```dockerfile
# stage2/Dockerfile.multistage
# ---- 阶段 1：构建 wheel ----
FROM python:3.11-slim AS builder
WORKDIR /app

# 装构建依赖（仅 builder 阶段需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 打包成 wheel 缓存
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- 阶段 2：运行时 ----
FROM python:3.11-slim AS runtime

# 安全：创建非 root 用户
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# 从 builder 拷贝 wheel 并安装
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# 拷贝应用代码
COPY --chown=app:app src/ ./src/

USER app
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 6. 关键指令解析

| 指令 | 作用 |
|------|------|
| `FROM ... AS <name>` | 命名阶段，供后续 `COPY --from=<name>` 引用 |
| `COPY --from=builder` | 从其他阶段拷贝文件 |
| `--no-cache-dir` | 不保留 pip 缓存，减小体积 |
| `--no-install-recommends` | apt 不装推荐包 |
| `rm -rf /var/lib/apt/lists/*` | 清空 apt 列表（每个 layer 都要清）|
| `USER <user>` | 切换非 root 用户（K8s 安全要求）|

## 7. 验证镜像大小

```bash
# 构建并对比
docker build -f Dockerfile.single -t app:single .
docker build -f Dockerfile.multistage -t app:multi .
docker images | grep app

# 预期：multi 比 single 小 30-50%
```

## 8. 练习任务

1. **对比镜像尺寸**：在 `stage1/Dockerfile.single` 和 `stage2/Dockerfile.multistage` 上分别构建一个 FastAPI demo，对比 `docker images` 输出的 SIZE 字段
2. **故意破坏缓存**：把 `COPY requirements.txt .` 改成 `COPY . /app` 再 `RUN pip install`，观察构建时间变化
3. **安全检查**：用 `docker run --rm app:multi whoami` 验证是否以非 root 运行（应输出 `app`）
4. **.dockerignore 验证**：故意把 `tests/` 留外面，跑 `docker run --rm app:multi ls /app` 看是否泄露

## 参考资料

- [Docker 多阶段构建官方文档](https://docs.docker.com/build/building/multi-stage/)
- [Dockerfile 最佳实践](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Python Docker 实战](https://pythonspeed.com/docker/)