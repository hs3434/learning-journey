# AMD ROCm Python 后端工程师学习计划

> 目标：2-3 周快速补齐 AMD ROCm Radeon Cloud 后端工程师技能短板
> 背景：3 年 Python（生信+BCI），熟悉 Docker/云原生/PyTorch/Transformer，缺 K8s 实战与大模型项目经验

## 岗位技能缺口分析

| 技能 | 现状 | 优先级 |
|------|------|--------|
| Python 后端（Django 基础） | 有基础，需扩展到 FastAPI + 异步 | 🔴 补齐 |
| Docker（多阶段构建、生产化） | 有基础，需深化 | 🔴 补齐 |
| Kubernetes（核心 + 实战） | 零基础 | 🔴 重点 |
| 大模型推理（vLLM/HF） | 有 PyTorch + Transformer 基础，无 LLM 项目 | 🔴 重点 |
| ROCm / GPU 集群 | 仅 CPU PyTorch | 🟡 核心 |
| 监控（Prometheus/Grafana） | 零基础 | 🟡 核心 |
| 前端（React/Vue 基础） | 零基础 | 🟢 加分 |
| 数据库/中间件（PostgreSQL/Redis/Kafka） | 有 MySQL/MinIO，缺 Redis/Kafka/PG | 🟢 加分 |

---

## 学习路线（6 周冲刺）

```
Week 1：Docker 深入 + K8s 核心
Week 2：K8s 进阶 + Python Web 部署
Week 3：FastAPI + Python 后端强化
Week 4：大模型推理服务（vLLM + HuggingFace）
Week 5：ROCm 入门 + 监控 + 前端基础
Week 6：整合项目 + 简历 + 面试准备
```

---

## Week 1：Docker 深入 + K8s 核心

### Week 1 目标
掌握 Docker 生产化最佳实践 + K8s 核心概念，能用 minikube 本地部署一个 Python Web 应用。

### 每日节奏（3-4h）：1h 理论 + 2h 项目 + 0.5-1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | Docker 多阶段构建、Dockerfile 优化、layer 缓存 | 重构 Snakemake 镜像为多阶段构建 |
| 2 | Docker Compose 多容器编排、网络、volume | docker-compose 跑通 Snakemake + MinIO + MySQL |
| 3 | K8s 架构（Control Plane / Node / Pod）、kubectl 基础 | minikube 启动 + kubectl get/describe/logs |
| 4 | Pod 生命周期、Deployment、ReplicaSet、滚动更新 | 部署 nginx Deployment，演示扩容/回滚 |
| 5 | Service 三种类型（ClusterIP/NodePort/LoadBalancer）、标签选择器 | 用 NodePort 暴露 nginx |
| 6 | ConfigMap + Secret + Volume 挂载 | 部署一个带配置的 Python FastAPI 应用 |
| 7 | 复盘 + 整合 | 产出：k8s-local-stack |

### Week1 配套项目：k8s-local-stack

```python
# projects/k8s-local-stack/
# minikube 本地部署一个 FastAPI + Redis 的 Python Web 应用

# --- Dockerfile（多阶段构建） ---
# --- Dockerfile ---
# FROM python:3.11-slim AS builder
# WORKDIR /app
# COPY requirements.txt .
# RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt
#
# FROM python:3.11-slim
# WORKDIR /app
# COPY --from=builder /wheels /wheels
# COPY --from=builder /app/requirements.txt .
# RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt
# COPY src/ ./src/
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- k8s/deployment.yaml ---
# apiVersion: apps/v1
# kind: Deployment
# metadata:
#   name: fastapi-app
# spec:
#   replicas: 3
#   selector:
#     matchLabels:
#       app: fastapi-app
#   template:
#     metadata:
#       labels:
#         app: fastapi-app
#     spec:
#       containers:
#       - name: app
#         image: fastapi-app:v1
#         ports:
#         - containerPort: 8000
#         envFrom:
#         - configMapRef:
#             name: app-config
#         - secretRef:
#             name: app-secret
#         resources:
#           requests:
#             memory: "128Mi"
#             cpu: "250m"
#           limits:
#             memory: "512Mi"
#             cpu: "500m"

# --- k8s/service.yaml ---
# apiVersion: v1
# kind: Service
# metadata:
#   name: fastapi-service
# spec:
#   type: NodePort
#   selector:
#     app: fastapi-app
#   ports:
#   - port: 8000
#     targetPort: 8000
#     nodePort: 30080

# --- src/main.py ---
from fastapi import FastAPI
import os

app = FastAPI(title="K8s Demo App")

@app.get("/")
def root():
    return {"message": "Hello from K8s", "pod": os.getenv("HOSTNAME")}

@app.get("/health")
def health():
    return {"status": "ok"}
```

---

## Week 2：K8s 进阶 + Python Web 部署

### Week 2 目标
掌握 K8s 进阶资源（Ingress/StatefulSet/PV），能用 Helm 或纯 YAML 部署一个带持久化的多服务应用。

### 每日节奏：1h 理论 + 2h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | Ingress（nginx ingress controller）、路由规则、TLS | 配置 Ingress 暴露 FastAPI，路径分流 |
| 2 | Namespace + ResourceQuota + LimitRange | 多环境隔离（dev/staging/prod）|
| 3 | StatefulSet vs Deployment、PV/PVC、StorageClass | 用 StatefulSet 部署 PostgreSQL + PVC |
| 4 | Job / CronJob（批处理、定时任务，对应 GPU 任务调度）| 用 Job 跑一个数据处理任务 |
| 5 | Helm 基础（Chart 结构、values.yaml、模板）| 用 Helm 部署 Prometheus |
| 6 | K8s 网络模型、CNI、Service Mesh 概念（Istio 简介）| 笔记 |
| 7 | 复盘 + 整合 | 产出：k8s-multi-service-stack |

### Week2 配套项目：k8s-multi-service-stack

```python
# projects/k8s-multi-service-stack/
# K8s 多服务应用：FastAPI + PostgreSQL + Redis + Nginx Ingress

# --- 项目结构 ---
# k8s-multi-service-stack/
# ├── helm/
# │   └── app/
# │       ├── Chart.yaml
# │       ├── values.yaml
# │       └── templates/
# │           ├── deployment.yaml
# │           ├── service.yaml
# │           ├── ingress.yaml
# │           ├── configmap.yaml
# │           └── secret.yaml
# ├── src/
# │   ├── main.py
# │   ├── db.py
# │   ├── cache.py
# │   └── models.py
# ├── docker-compose.yml       # 本地开发
# └── README.md

# --- src/main.py ---
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .db import get_db, engine
from . import models, cache

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Multi-Service Demo")

@app.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)):
    # 先查 Redis 缓存
    cached = cache.get_item(item_id)
    if cached:
        return {"source": "cache", "data": cached}

    # 再查 PostgreSQL
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item:
        cache.set_item(item_id, item.name)
        return {"source": "db", "data": item.name}
    return {"error": "not found"}

@app.post("/items")
def create_item(name: str, db: Session = Depends(get_db)):
    item = models.Item(name=name)
    db.add(item)
    db.commit()
    db.refresh(item)
    cache.invalidate_all()
    return {"id": item.id, "name": item.name}

# --- src/db.py ---
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://user:pass@postgres:5432/appdb"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- src/cache.py ---
import redis
import json

r = redis.Redis(host='redis', port=6379, db=0)

def get_item(item_id: int):
    val = r.get(f"item:{item_id}")
    return json.loads(val) if val else None

def set_item(item_id: int, name: str, ttl=300):
    r.setex(f"item:{item_id}", ttl, json.dumps(name))

def invalidate_all():
    r.flushdb()
```

---

## Week 3：FastAPI + Python 后端强化

### Week 3 目标
把 Django 经验迁移到 FastAPI，掌握异步 Python、依赖注入、数据库 ORM、中间件集成。

### 每日节奏：1h 理论 + 2h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | FastAPI 路由、Pydantic 模型、自动 OpenAPI 文档 | 重写一个 Django view 为 FastAPI |
| 2 | 异步 asyncio、async/await、异步数据库（asyncpg）| 写一个并发请求处理器 |
| 3 | SQLAlchemy 2.0 + Alembic 迁移 | 数据库 ORM + 迁移脚本 |
| 4 | Redis 客户端（redis-py async）+ 缓存策略 | 实现 cache-aside 模式 |
| 5 | Kafka 概念 + aiokafka 生产消费 | 简单事件流 demo |
| 6 | 中间件、异常处理、日志（loguru）| 统一错误处理 + 请求追踪 |
| 7 | 复盘 + 项目整合 | 产出：fastapi-backend-template |

### Week3 配套项目：fastapi-backend-template

```python
# projects/fastapi-backend-template/
# 现代化 Python 后端模板：FastAPI + 异步 + PostgreSQL + Redis + Kafka

# --- 项目结构 ---
# fastapi-backend-template/
# ├── src/
# │   ├── main.py              # FastAPI 入口
# │   ├── config.py            # 配置（pydantic-settings）
# │   ├── api/
# │   │   ├── deps.py          # 依赖注入
# │   │   └── v1/
# │   │       ├── endpoints/
# │   │       │   ├── users.py
# │   │       │   └── tasks.py
# │   │       └── router.py
# │   ├── core/
# │   │   ├── security.py      # JWT / OAuth2
# │   │   ├── logging.py       # loguru
# │   │   └── exceptions.py
# │   ├── db/
# │   │   ├── base.py          # SQLAlchemy Base
# │   │   ├── session.py       # async session
│   │   └── models/
# │   ├── schemas/             # Pydantic schemas
# │   ├── services/            # 业务逻辑层
# │   ├── cache/               # Redis 封装
# │   └── messaging/           # Kafka 封装
# ├── alembic/                 # 数据库迁移
# ├── tests/                   # pytest + httpx
# ├── Dockerfile
# ├── docker-compose.yml
# └── pyproject.toml

# --- src/main.py ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .api.v1.router import api_router
from .core.logging import configure_logging
from .db.session import engine
from .cache.redis_client import redis_client

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    await redis_client.connect()
    yield
    # 关闭
    await redis_client.disconnect()
    await engine.dispose()

app = FastAPI(
    title="Backend Template",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}

# --- src/config.py ---
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "backend-template"
    DEBUG: bool = False

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "pass"
    POSTGRES_DB: str = "appdb"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
```

---

## Week 4：大模型推理服务

### Week 4 目标
能基于 Hugging Face / vLLM / Ollama 部署一个大模型推理 API 服务，并容器化 + K8s 部署。

### 每日节奏：1.5h 理论 + 2h 项目 + 0.5h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | Transformer 回顾、HF Transformers 库（AutoModel/AutoTokenizer）| 加载 Qwen2.5-0.5B-Instruct 跑通 generate |
| 2 | 模型量化（INT8/INT4/GGUF）、bitsandbytes、GPTQ | 量化加载 7B 模型 |
| 3 | vLLM 架构（PagedAttention）、推理部署、continuous batching | vLLM 部署 Qwen2.5-7B，提供 OpenAI 兼容 API |
| 4 | Ollama 本地部署、Modelfile 自定义 | Ollama 跑通 Llama3 |
| 5 | 推理服务化：FastAPI + vLLM 封装、流式输出（SSE）| 写一个支持流式的推理 API |
| 6 | AMD ROCm 容器镜像（rocm/pytorch）+ HF 模型 | 用 ROCm 镜像跑通推理 |
| 7 | 复盘 + 整合 | 产出：llm-inference-service |

### Week4 配套项目：llm-inference-service

```python
# projects/llm-inference-service/
# 大模型推理服务：FastAPI + vLLM + Docker + K8s + ROCm 镜像

# --- 项目结构 ---
# llm-inference-service/
# ├── src/
# │   ├── main.py              # FastAPI 入口
# │   ├── llm/
# │   │   ├── vllm_engine.py   # vLLM 封装
# │   │   └── prompts.py       # Prompt 模板
# │   ├── api/
# │   │   └── completions.py   # /v1/completions 兼容 OpenAI
# │   └── schemas.py
# ├── k8s/
# │   ├── deployment.yaml
# │   ├── service.yaml
│   │   ├── ingress.yaml
# │   └── gpu-resource.yaml    # AMD GPU 资源
# ├── Dockerfile               # 基于 rocm/pytorch
# └── README.md

# --- src/llm/vllm_engine.py ---
from vllm import LLM, SamplingParams
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

class VLLMEngine:
    """vLLM 推理引擎封装"""

    def __init__(
        self,
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        tensor_parallel_size: int = 1,
        dtype: str = "float16",
    ):
        self.llm = LLM(
            model=model,
            tensor_parallel_size=tensor_parallel_size,
            dtype=dtype,
            trust_remote_code=True,
        )
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def generate(
        self,
        prompts: List[str],
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False,
    ) -> List[str]:
        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        loop = asyncio.get_event_loop()
        outputs = await loop.run_in_executor(
            self.executor,
            lambda: self.llm.generate(prompts, sampling_params)
        )
        return [o.outputs[0].text for o in outputs]


# --- src/main.py ---
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from .llm.vllm_engine import VLLMEngine
from .schemas import CompletionRequest

app = FastAPI(title="LLM Inference Service")
engine: VLLMEngine = None  # 启动时初始化

@app.on_event("startup")
async def startup():
    global engine
    engine = VLLMEngine()

@app.post("/v1/completions")
async def completions(req: CompletionRequest):
    """OpenAI 兼容接口"""
    results = await engine.generate(
        prompts=[req.prompt],
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    return {"choices": [{"text": results[0]}]}

@app.post("/v1/chat/completions")
async def chat(req: ChatRequest):
    """OpenAI 兼容聊天接口"""
    prompt = format_chat_prompt(req.messages)
    results = await engine.generate(prompts=[prompt])
    return {
        "choices": [{
            "message": {"role": "assistant", "content": results[0]}
        }]
    }

# --- k8s/deployment.yaml ---
# apiVersion: apps/v1
# kind: Deployment
# metadata:
#   name: llm-inference
# spec:
#   replicas: 1
#   selector:
#     matchLabels:
#       app: llm-inference
#   template:
#     metadata:
#       labels:
#         app: llm-inference
#     spec:
#       containers:
#       - name: llm
#         image: llm-inference:latest
#         ports:
#         - containerPort: 8000
#         resources:
#           requests:
#             amd.com/gpu: 1
#             memory: "16Gi"
#           limits:
#             amd.com/gpu: 1
#             memory: "32Gi"
#         env:
#         - name: MODEL_NAME
#           value: "Qwen/Qwen2.5-7B-Instruct"
```

---

## Week 5：ROCm 入门 + 监控 + 前端基础

### Week 5 目标
理解 ROCm 生态与 AMD GPU 编程，部署 Prometheus + Grafana 监控，掌握基础前端（HTML/JS/React）。

### 每日节奏：1h 理论 + 2h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | ROCm 架构、HIP vs CUDA、AMD GPU 产品线（Instinct MI 系列）| 阅读 ROCm 官方 Quick Start |
| 2 | PyTorch + ROCm 镜像、torch.cuda.is_available() 等价 API | 在 ROCm 容器跑通 MNIST/CIFAR |
| 3 | Prometheus 架构、metrics、scrape 配置、PromQL | 部署 Prometheus + node-exporter |
| 4 | Grafana 面板、告警规则、K8s 监控集成 | 配置 LLM 服务监控面板（GPU 利用率、QPS、延迟）|
| 5 | 前端基础：HTML/CSS/JavaScript ES6+ | 写一个推理服务的简单 Web UI |
| 6 | React 入门（组件、Hooks、状态管理）| 用 React 重写前端页面 |
| 7 | 复盘 + 整合 | 产出：llm-platform-mvp |

### Week5 配套项目：llm-platform-mvp

```python
# projects/llm-platform-mvp/
# LLM 推理平台 MVP：FastAPI 后端 + React 前端 + Prometheus 监控 + ROCm 推理

# --- 项目结构 ---
# llm-platform-mvp/
# ├── backend/                  # Week 4 的推理服务
# │   ├── src/
# │   └── k8s/
# ├── frontend/                 # React + Vite
# │   ├── src/
# │   │   ├── App.jsx
# │   │   ├── components/
# │   │   │   ├── ChatWindow.jsx
# │   │   │   └── ModelSelector.jsx
# │   │   └── api/
# │   │       └── client.js
# │   ├── package.json
# │   └── vite.config.js
# ├── monitoring/
# │   ├── prometheus.yml
# │   ├── grafana-dashboard.json
│   │   └── alert-rules.yaml
# └── README.md

# --- frontend/src/App.jsx ---
import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import ModelSelector from './components/ModelSelector'
import { chatCompletion } from './api/client'

function App() {
  const [model, setModel] = useState('Qwen2.5-7B-Instruct')
  const [messages, setMessages] = useState([])

  const handleSend = async (userMessage) => {
    const newMessages = [...messages, { role: 'user', content: userMessage }]
    setMessages(newMessages)

    const response = await chatCompletion(model, newMessages)
    setMessages([...newMessages, { role: 'assistant', content: response }])
  }

  return (
    <div className="app">
      <header>
        <h1>AMD ROCm LLM Platform</h1>
        <ModelSelector value={model} onChange={setModel} />
      </header>
      <ChatWindow messages={messages} onSend={handleSend} />
    </div>
  )
}

export default App

# --- frontend/src/api/client.js ---
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function chatCompletion(model, messages) {
  const res = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages }),
  })
  const data = await res.json()
  return data.choices[0].message.content
}

# --- monitoring/prometheus.yml ---
# global:
#   scrape_interval: 15s
# scrape_configs:
#   - job_name: 'llm-inference'
#     static_configs:
#       - targets: ['llm-inference:8000']
#   - job_name: 'node-exporter'
#     static_configs:
#       - targets: ['node-exporter:9100']
#   - job_name: 'gpu-exporter'
#     static_configs:
#       - targets: ['amd-gpu-exporter:9835']

# --- monitoring/alert-rules.yaml ---
# groups:
# - name: llm-service
#   rules:
#   - alert: HighGPUMemory
#     expr: amd_gpu_memory_used_bytes / amd_gpu_memory_total_bytes > 0.9
#     for: 5m
#     annotations:
#       summary: "GPU memory usage above 90%"
#   - alert: HighRequestLatency
#     expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
#     for: 5m
#     annotations:
#       summary: "P95 latency above 5s"
```

---

## Week 6：整合项目 + 简历 + 面试准备

### Week 6 目标
完成"基于 K8s 的 LLM 推理平台"整合项目，调整简历，准备面试。

### 每日节奏：2h 项目 + 1h 文档 + 1h 复盘

| Day | 任务 |
|-----|------|
| 1 | 整合 K8s 部署：FastAPI 后端 + React 前端 + Prometheus 监控 |
| 2 | Helm Chart 打包（可选），一键部署 |
| 3 | 编写完整 README + 架构图（draw.io）+ 演示视频 |
| 4 | 简历调整：定位切换为"Python 后端 + AI 基础设施工程师" |
| 5 | 整理 GitHub 仓库（README、截图、demo）|
| 6 | 准备 10 个 K8s 面试题（Pod 调度、Service vs Ingress、StatefulSet vs Deployment、GPU 调度、Helm 原理）|
| 7 | 准备 5 个 Python 后端面试题（asyncio 原理、FastAPI 依赖注入、GIL、装饰器、生成器）|

### Week6 配套产出：portfolio 项目

```
portfolio/
├── k8s-llm-platform/          # 主项目：基于 K8s 的 LLM 推理平台
│   ├── backend/               # FastAPI + vLLM
│   ├── frontend/              # React Web UI
│   ├── monitoring/            # Prometheus + Grafana
│   ├── k8s/                   # 完整 K8s manifests + Helm
│   ├── docker-compose.yml     # 本地开发
│   ├── README.md              # 项目介绍 + 架构图
│   └── DEMO.md                # 演示步骤
├── snakemake-to-argo/         # 副项目：工作流引擎迁移（Snakemake → Argo）
│   └── README.md
└── RESUME.md                  # 调整后的简历
```

### 简历核心调整

| 调整项 | 原表述 | 新表述 |
|--------|--------|--------|
| 求职意向 | 脑机接口软件工程师 | Python 后端工程师 / AI 基础设施工程师 |
| Snakemake 框架 | 生信工作流 | 自研工作流引擎（可类比 Argo Workflows）|
| MinIO | 数据存储 | 对象存储服务化（K8s PV 后端）|
| PyTorch Transformer | EEG 解码 | 大模型架构经验（GPT/BERT/RoPE/Pre-LN），具备 HF Transformers 迁移能力 |
| 弱化项 | BCI/EEG/MNE | 弱化或仅作为"AI 应用案例"一句话提及 |

---

## 重要资源

| 资源 | 地址 |
|------|------|
| Kubernetes 官方文档 | https://kubernetes.io/zh-cn/docs/home/ |
| minikube | https://minikube.sigs.k8s.io/ |
| K8s 中文实战（阳明 K8s 笔记）| https://www.yuque.com/xiangguo/it3aew/ |
| FastAPI 官方文档 | https://fastapi.tiangolo.com/zh/ |
| Hugging Face Transformers | https://huggingface.co/docs/transformers |
| vLLM 文档 | https://docs.vllm.ai/ |
| Ollama | https://ollama.com/ |
| AMD ROCm 文档 | https://rocm.docs.amd.com/ |
| AMD ROCm GitHub | https://github.com/ROCm |
| Prometheus 官方文档 | https://prometheus.io/docs/ |
| Grafana 官方文档 | https://grafana.com/docs/ |
| React 官方文档 | https://react.dev/ |

---

## 复盘模板（每周结束填写）

```markdown
## WeekX 复盘
### 完成 vs 计划
-
### 核心问题
-
### 下周调整
-
```

---

## 时间线总览

```
Week 1 ──── K8s 核心 + Docker 深入      → k8s-local-stack
Week 2 ──── K8s 进阶 + 多服务部署       → k8s-multi-service-stack
Week 3 ──── FastAPI + Python 后端强化   → fastapi-backend-template
Week 4 ──── 大模型推理服务              → llm-inference-service
Week 5 ──── ROCm + 监控 + 前端          → llm-platform-mvp
Week 6 ──── 整合项目 + 简历 + 面试      → portfolio + K8s/Python 面试题
```