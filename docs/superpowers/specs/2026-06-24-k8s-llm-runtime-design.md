# k8s-llm-runtime — 设计稿

**日期**：2026-06-24
**状态**：待审阅
**目标**：从 ai-flow 抽出 K8s 执行能力为独立 Python 库 `k8s-llm-runtime`，并基于此库构建 vLLM 推理服务网关（Model Serving Router），作为 AMD ROCm Python 后端岗的面试项目。

> **范围**：本文档定义一个新仓库 `k8s-llm-runtime` 的完整设计。ai-flow **不修改**。

## 背景与目标

### 起源

ai-flow（`/work/run/projects/bio-24/my_projects/ai-flow/`）是一个分布式分析工作流平台，包含 `executor/k8s_executor.py` 用 `kubernetes-python-client` 封装 K8s Job 调度。当前匹配 AMD ROCm Python 后端岗的 JD（见 `tracks/amd-rocm-python-backend/notes/job-requirements.md`）有两大缺口：

1. **ai-flow 缺少 LLM 推理能力**（无 vLLM、无 transformers）
2. **ai-flow 的 K8s 能力与具体业务（流程编排）耦合**，难以作为独立"调度框架"对外展示

### 目标

抽离 ai-flow 的 K8s 能力为**独立 Python 库**，并在其之上构建**面向用户的 vLLM 推理服务网关**：

- 用户发 `POST /v1/chat/completions`（OpenAI 兼容）
- 网关在后台按需 `helm install` 部署对应模型
- 部署完成后转发请求并返回响应
- 用户**完全不需要知道 K8s 存在**

### 适配 JD 关键需求

| JD 要求 | 本项目对应物 |
|---|---|
| 容器化部署、资源调度、任务编排、集群运维 | `K8sJobOperator` + Helm chart |
| 平台型软件后端研发 | `ModelOperator` + FastAPI Router |
| 大模型训练/推理 Workshop、教程、功能演示 | `examples/vllm-qwen/`（vLLM 推理服务） |
| Python 后端 2 年+ | FastAPI + Pydantic + 类型化异常 |
| Docker/k8s 部署经验 | Docker multi-stage + Helm chart + Kustomize-friendly |
| AMD ROCm 加分项 | `gpu.vendor=amd` + `amd.com/gpu` 资源调度 |

---

## 设计决策

| 维度 | 决策 | 理由 |
|---|---|---|
| 仓库位置 | **完全独立仓库** `/work/run/projects/bio-24/my_projects/k8s-llm-runtime/` | 与 ai-flow 解耦；可单独发版；面试时独立作品 |
| Python 版本 | ≥ 3.11 | 与 ai-flow / learning-journey 一致 |
| 包管理 | `uv` | 与 learning-journey 风格一致 |
| K8s 客户端 | `kubernetes>=29`（官方 Python client）| 标准 |
| Manifests 形式 | **Helm chart**（非裸 YAML / Kustomize）| Helm 是 K8s 生态事实标准；图表参数化利于多环境多模型 |
| Python lib API 风格 | **三层分层**（低/中/高）| 职责清晰，可单独使用可组合 |
| Demo 形态 | vLLM 推理服务（无训练 pipeline）| 用户明确选择"聚焦推理" |
| Router 部署位置 | **仅 K8s 内**（charts/llm-router）| 用户明确选择；生产模式；in-cluster config 自动认证 |
| GPU vendor 选择 | **values.yaml 显式 `gpu.vendor`**（amd/nvidia/none）| 显式优于隐式；chart 不能在 install 时探测集群 |
| 分布式锁 | **K8s Lease**（coordination.k8s.io/v1）| 多 Router replica 防并发部署同一模型 |
| Helm 调用方式 | **`helm` CLI subprocess** | 稳定；AMD ROCm 集群 helm 是预装标准件 |
| 错误处理 | **类型化异常 + tenacity 重试 + HTTP 状态码映射** | 库-服务边界清晰 |
| 可观测性 | **structlog JSON + prometheus_client + 可选 ServiceMonitor** | K8s 原生采集 |
| 测试金字塔 | 4 层：unit / chart / integration / lint | 速度与覆盖平衡 |
| CI | GitHub Actions（unit+chart 每次 push；integration 仅 main + nightly）| 控制 CI 时间 |
| 并发模型 | FastAPI async + httpx async client | I/O 密集（K8s API / vLLM 转发）适合 async |

---

## 仓库架构与目录布局

### 仓库元信息

- **名称**：`k8s-llm-runtime`
- **位置**：`/work/run/projects/bio-24/my_projects/k8s-llm-runtime/`
- **许可证**：MIT
- **Python**：≥ 3.11

### 目录树

```
k8s-llm-runtime/
├── AGENTS.md                       # 开发规范
├── README.md                       # 项目介绍 + Quickstart
├── Makefile                        # make cluster-up / demo / lint / test
├── pyproject.toml                  # uv/pip 双兼容
├── docker/
│   └── Dockerfile.router           # Router 镜像（multi-stage）
├── src/
│   └── k8s_llm_runtime/
│       ├── __init__.py
│       ├── types.py                # Pydantic 模型（公共类型）
│       ├── job.py                  # K8sJobOperator（低层）
│       ├── vllm.py                 # VLLMInferenceOperator（中层）
│       ├── model.py                # ModelOperator（高层）[核心]
│       ├── lock.py                 # K8sLeaseLock（分布式锁）
│       ├── errors.py               # 类型化异常
│       ├── _client.py              # K8s client 单例封装
│       ├── _retry.py               # tenacity 重试封装
│       ├── _log.py                 # structlog 配置
│       └── _metrics.py             # Prometheus 指标定义
├── charts/
│   ├── llm-inference/              # Layer 2: vLLM 推理负载
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── templates/
│   │       ├── _helpers.tpl
│   │       ├── deployment.yaml
│   │       ├── service.yaml
│   │       ├── ingress.yaml
│   │       ├── hpa.yaml
│   │       ├── serviceaccount.yaml
│   │       ├── configmap.yaml
│   │       ├── servicemonitor.yaml
│   │       ├── poddisruptionbudget.yaml
│   │       └── NOTES.txt
│   └── llm-router/                 # Layer 3: Router 服务 [NEW]
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── _helpers.tpl
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── ingress.yaml
│           ├── serviceaccount.yaml
│           ├── role.yaml
│           ├── rolebinding.yaml
│           ├── configmap.yaml      # 挂载模型别名字典
│           ├── hpa.yaml
│           └── servicemonitor.yaml
├── examples/
│   └── vllm-qwen/
│       ├── server.py               # FastAPI Router 入口
│       ├── client.py               # 外部测试客户端
│       ├── benchmark.py            # 并发压测
│       └── test_request.json
├── scripts/
│   └── cluster/                    # Layer 1: 集群安装
│       ├── kind-up.sh
│       ├── minikube-up.sh
│       ├── kind-down.sh
│       ├── minikube-down.sh
│       ├── kind-config.yaml        # 多节点 kind 配置
│       └── common/
│           ├── install-nginx.sh
│           └── install-metrics-server.sh
├── tests/
│   ├── unit/
│   │   ├── conftest.py
│   │   ├── test_types.py
│   │   ├── test_job.py
│   │   ├── test_vllm.py
│   │   ├── test_model.py
│   │   ├── test_lock.py
│   │   └── test_server.py
│   ├── chart/
│   │   ├── conftest.py
│   │   ├── test_llm_inference.py
│   │   ├── test_llm_router.py
│   │   └── snapshots/
│   │       ├── llm_inference_default.yaml
│   │       ├── llm_inference_amd.yaml
│   │       ├── llm_inference_nvidia.yaml
│   │       ├── llm_inference_cpu.yaml
│   │       └── llm_router_default.yaml
│   └── integration/
│       ├── conftest.py
│       ├── test_helpers.py
│       ├── test_job_e2e.py
│       ├── test_vllm_e2e.py
│       ├── test_model_e2e.py
│       └── test_server_e2e.py
├── docs/
│   ├── architecture.md
│   ├── amd-interview-demo.md       # 面试 demo 步骤
│   └── diagrams/
│       ├── architecture.svg
│       └── demo-flow.svg
└── .github/
    └── workflows/
        ├── ci.yml                  # lint + unit + chart
        └── integration.yml         # kind e2e（手动触发 + nightly）
```

---

## 关键依赖

| 依赖 | 用途 |
|---|---|
| `kubernetes>=29` | K8s Python 客户端 |
| `pydantic>=2` | JobSpec / values 类型化 |
| `structlog` | JSON 结构化日志 |
| `prometheus_client` | 指标 |
| `tenacity` | 重试 |
| `httpx` | async HTTP（vLLM 转发） |
| `pyyaml` | Helm values 渲染 |
| `fastapi` + `uvicorn` | Router Web 框架 |
| `openai` (可选) | client.py 兼容 OpenAI SDK |
| dev: `pytest`, `pytest-asyncio`, `pytest-mock`, `pytest-cov`, `ruff`, `mypy`, `respx` | 测试与质量 |

外部命令依赖：`helm`（在 Router 容器内和开发机都需安装）。

---

## Python lib API 设计（三层 + 基础类型）

### Layer 0 — `types.py`：Pydantic 模型

```python
# src/k8s_llm_runtime/types.py
from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class GPUVendor(str, Enum):
    NONE = "none"
    NVIDIA = "nvidia"
    AMD = "amd"


class GPUResource(BaseModel):
    vendor: GPUVendor = GPUVendor.NONE
    limit: int = 1


class ResourceSpec(BaseModel):
    cpu_request: str = "1"
    cpu_limit: str = "2"
    memory_request: str = "1Gi"
    memory_limit: str = "2Gi"
    gpu: GPUResource = GPUResource()


class ContainerSpec(BaseModel):
    image: str
    command: Optional[list[str]] = None
    args: Optional[list[str]] = None
    env: dict[str, str] = Field(default_factory=dict)
    resources: ResourceSpec = ResourceSpec()
    ports: list[int] = Field(default_factory=list)


class JobSpec(BaseModel):
    name: str
    namespace: str = "default"
    container: ContainerSpec
    service_account: Optional[str] = None
    ttl_seconds_after_finished: int = 3600
    backoff_limit: int = 3
    restart_policy: Literal["Never", "OnFailure"] = "Never"


class JobStatus(BaseModel):
    name: str
    phase: Literal["pending", "running", "succeeded", "failed"]
    active: int = 0
    succeeded: int = 0
    failed: int = 0
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
```

### Layer 1 — `job.py`：`K8sJobOperator`（低层）

```python
class K8sJobOperator:
    def __init__(self, namespace: str = "default", kubeconfig: Optional[str] = None): ...
    def create(self, spec: JobSpec) -> str: ...
    def get_status(self, job_name: str) -> JobStatus: ...
    def get_logs(self, job_name: str, tail_lines: int = 200) -> str: ...
    def delete(self, job_name: str, propagation: Literal["foreground", "background"] = "foreground") -> None: ...
    def wait_for_completion(self, job_name: str, timeout: int = 3600, poll_interval: int = 10) -> JobStatus: ...
```

**与 ai-flow 现状对比**（取自 `ai-flow/src/backend/ai_flow/executor/k8s_executor.py`）：

| 改进点 | 旧（ai-flow）| 新（k8s-llm-runtime）|
|---|---|---|
| API 风格 | 函数 + 单例 + 类代理 | 显式 `K8sJobOperator` 实例（更好测试）|
| 入参 | 大量位置参数 + dict 透传 | 强类型 `JobSpec` |
| GPU 资源 | 仅 `nvidia.com/gpu` | **支持 `amd.com/gpu`** |
| 返回 | 字典 | `JobStatus` Pydantic 模型 |
| 错误处理 | `raise` 裸异常 | 类型化异常（`errors.py`）|
| kubeconfig | 只读 `~/.kube/config` | 支持自定义路径 + in-cluster 兜底 |

### Layer 2 — `vllm.py`：`VLLMInferenceOperator`（中层）

```python
@dataclass
class VLLMDeployment:
    release_name: str
    namespace: str
    model_name: str
    endpoint: str
    phase: Literal["pending", "deploying", "ready", "failed"]
    message: Optional[str] = None
    replicas_ready: int = 0


class VLLMInferenceOperator:
    def __init__(self, chart_path: str = "./charts/llm-inference", kubeconfig: Optional[str] = None): ...
    def deploy(self, release_name: str, model_name: str, namespace: str = "default",
               gpu: GPUResource = GPUResource(vendor=GPUVendor.AMD, limit=1),
               replicas: int = 1, timeout: int = 600) -> VLLMDeployment: ...
    def undeploy(self, release_name: str, namespace: str) -> None: ...
    def get_status(self, release_name: str, namespace: str) -> VLLMDeployment: ...
    def get_endpoint(self, release_name: str, namespace: str) -> str: ...
```

**实现依赖**：内部用 `helm` CLI（subprocess）；不抽 pure-Python helm lib（YAGNI）。

### Layer 3 — `model.py`：`ModelOperator`（高层）[核心]

```python
from pydantic import BaseModel, ConfigDict


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model: str                          # 用户用的别名，如 "qwen-7b"
    messages: list[ChatMessage]
    temperature: float = 1.0
    max_tokens: int = 1024
    stream: bool = False


class ChatResponse(BaseModel):
    # 透传 vLLM / OpenAI 的所有字段，未声明字段宽松放行
    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]
    usage: dict


class ModelOperator:
    def __init__(self, model_aliases: dict[str, str],
                 vllm_op: VLLMInferenceOperator,
                 namespace: str = "llm-models",
                 default_gpu: GPUResource = GPUResource(vendor=GPUVendor.AMD, limit=1),
                 default_replicas: int = 1,
                 idle_timeout_seconds: int = 0,
                 deploy_lock_ttl: int = 600): ...

    async def chat(self, req: ChatRequest) -> ChatResponse:
        """主入口：alias 解析 → 检查/部署 → 转发 → 返回"""

    async def list_models(self) -> list[str]: ...

    async def unload(self, alias: str) -> None: ...

    async def cleanup_idle(self) -> int: ...
```

**核心 chat 流程**：

```python
async def chat(self, req):
    # 1. alias 解析
    hf_model = self.model_aliases.get(req.model)
    if not hf_model:
        raise ModelNotFoundError(req.model)

    # 2. distributed lock 防并发部署
    async with K8sLeaseLock(key=f"deploy-{req.model}", namespace=self.namespace,
                            ttl=self.deploy_lock_ttl):
        # 3. 检查是否已部署
        status = self.vllm_op.get_status(req.model, self.namespace)
        if status.phase != "ready":
            # 4. 部署
            status = self.vllm_op.deploy(req.model, hf_model, self.namespace,
                                          gpu=self.default_gpu,
                                          replicas=self.default_replicas)

    # 5. 转发到 vLLM
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{status.endpoint}/v1/chat/completions",
            json=req.model_dump(exclude_none=True),
            timeout=300.0,
        )
        r.raise_for_status()
        return ChatResponse.model_validate(r.json())
```

### `lock.py`：`K8sLeaseLock`

```python
class K8sLeaseLock:
    def __init__(self, key: str, namespace: str, ttl: int = 600): ...
    async def __aenter__(self) -> "K8sLeaseLock":
        await self.acquire()
        return self
    async def __aexit__(self, *exc): await self.release()
    async def acquire(self) -> bool: ...   # 失败抛 LockAcquireTimeoutError
    async def release(self) -> None: ...
    async def renew(self) -> None: ...
```

### `errors.py`：类型化异常

```python
class K8sLLMRuntimeError(Exception): pass

class JobCreationError(K8sLLMRuntimeError): pass
class JobTimeoutError(K8sLLMRuntimeError): pass
class JobLogRetrievalError(K8sLLMRuntimeError): pass

class VLLMDeployError(K8sLLMRuntimeError): pass
class VLLMDeployTimeoutError(VLLMDeployError): pass
class VLLMUndeployError(K8sLLMRuntimeError): pass

class ModelNotFoundError(K8sLLMRuntimeError): pass
class ModelAliasError(K8sLLMRuntimeError): pass
class LockAcquireTimeoutError(K8sLLMRuntimeError): pass
```

---

## Helm Chart 设计

### 双 chart 职责划分

| Chart | 部署什么 | 谁部署 |
|---|---|---|
| `llm-inference` | vLLM 推理 Pod（一份 release = 一个模型）| `VLLMInferenceOperator` 自动调 |
| `llm-router` | Model Router 服务（FastAPI server.py）| 用户/运维手动 `helm install` |

### `charts/llm-inference/` 关键 values.yaml

```yaml
replicaCount: 1

image:
  repository: vllm/vllm-openai
  tag: latest
  pullPolicy: IfNotPresent

model:
  name: Qwen/Qwen2.5-0.5B-Instruct
  hfTokenSecret: ""

gpu:
  vendor: none                # none | amd | nvidia
  limit: 1

resources:
  requests: { cpu: "2", memory: "8Gi" }
  limits:   { cpu: "8", memory: "16Gi" }

vllm:
  args: []
  port: 8000

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: false
  className: nginx
  host: llm.local

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 3
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

serviceMonitor:
  enabled: false
  interval: 30s

nodeSelector: {}
tolerations: []
affinity: {}
```

### GPU vendor 选择机制

`templates/deployment.yaml` 关键片段：

```yaml
resources:
  limits:
    cpu: {{ .Values.resources.limits.cpu | quote }}
    memory: {{ .Values.resources.limits.memory | quote }}
    {{- if eq .Values.gpu.vendor "amd" }}
    amd.com/gpu: {{ .Values.gpu.limit | quote }}
    {{- end }}
    {{- if eq .Values.gpu.vendor "nvidia" }}
    nvidia.com/gpu: {{ .Values.gpu.limit | quote }}
    {{- end }}
```

### 三种部署模式示例

```bash
# CI 跑 CPU
helm install llm-demo ./charts/llm-inference \
  --set gpu.vendor=none --set model.name=Qwen/Qwen2.5-0.5B-Instruct

# AMD ROCm 生产 demo
helm install llm-demo ./charts/llm-inference \
  --set gpu.vendor=amd --set model.name=Qwen/Qwen2.5-7B-Instruct \
  --set nodeSelector."amd\.com/gpu\.product"=AMD_Instinct_MI300X

# NVIDIA 兜底
helm install llm-demo ./charts/llm-inference \
  --set gpu.vendor=nvidia --set model.name=meta-llama/Llama-3-8B-Instruct
```

### `charts/llm-router/` 关键 values.yaml

```yaml
replicaCount: 2

image:
  repository: k8s-llm-runtime/router
  tag: "0.1.0"

models:
  aliases:
    qwen-7b:   Qwen/Qwen2.5-7B-Instruct
    qwen-0.5b: Qwen/Qwen2.5-0.5B-Instruct
  defaultGpu:
    vendor: amd
    limit: 1
  idleTimeoutSeconds: 600
  deployLockTtl: 600

targetNamespace: llm-models

rbac:
  create: true
  rules:
    - apiGroups: ["apps"]
      resources: ["deployments", "replicasets"]
      verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
    - apiGroups: [""]
      resources: ["services", "pods", "configmaps"]
      verbs: ["get", "list", "watch"]
    - apiGroups: ["coordination.k8s.io"]
      resources: ["leases"]
      verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: true
  className: nginx
  host: router.local

resources:
  requests: { cpu: "500m", memory: "256Mi" }
  limits:   { cpu: "2",    memory: "1Gi" }

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70

serviceMonitor:
  enabled: false
```

### ConfigMap 注入模型别名

Router Deployment 挂载 `models-config` ConfigMap 到 `/app/config/models.yaml`；启动时读取构建 `ModelOperator.model_aliases`。

### 部署拓扑

```
┌──────────────────────────────────┐
│ namespace: llm-system            │
│ Deployment: llm-router           │
│  ├─ ServiceAccount: llm-router   │
│  └─ RBAC: manage Deployments     │
└──────────────────────────────────┘
                │
                │ (按需 helm install)
                ▼
┌─────────────────────────────────────────────┐
│ namespace: llm-models                       │
│ ┌─ Helm release: qwen-7b ─────────────────┐ │
│ │  Deployment + Service + ConfigMap        │ │
│ └─────────────────────────────────────────┘ │
│ ┌─ Helm release: llama-3-8b ──────────────┐ │
│ │  Deployment + Service + ConfigMap        │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## Demo 结构（server.py + client.py）

### server.py 端点（OpenAI 兼容）

| 方法 | 路径 | 作用 |
|---|---|---|
| POST | `/v1/chat/completions` | 核心：路由 chat 请求，自动按需部署 |
| GET | `/v1/models` | 列出当前已加载的模型 |
| GET | `/v1/models/{alias}` | 单个模型详情 |
| DELETE | `/v1/models/{alias}` | 主动卸载（helm uninstall）|
| GET | `/healthz` | liveness |
| GET | `/readyz` | readiness（含 K8s API 连通性）|
| GET | `/metrics` | Prometheus 指标 |

**不做**（YAGNI）：鉴权（demo 范围；生产在 ingress 层加 OAuth2）、流式响应、多模态。

### server.py 关键片段

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    aliases = load_model_aliases(Path("/app/config/models.yaml"))
    vllm_op = VLLMInferenceOperator(chart_path="/app/charts/llm-inference")
    app.state.op = ModelOperator(
        model_aliases=aliases, vllm_op=vllm_op,
        namespace=os.environ.get("TARGET_NAMESPACE", "llm-models"),
        default_gpu=GPUResource(vendor=GPUVendor(os.environ.get("GPU_VENDOR", "amd")),
                                limit=int(os.environ.get("GPU_LIMIT", "1"))),
        idle_timeout_seconds=int(os.environ.get("IDLE_TIMEOUT", "600")),
    )
    yield

app = FastAPI(title="LLM Router", version="0.1.0", lifespan=lifespan)


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    try:
        return await app.state.op.chat(req)
    except ModelNotFoundError:
        raise HTTPException(404, f"Unknown model alias: {req.model}")
    except VLLMDeployTimeoutError as e:
        raise HTTPException(503, f"Model deploy timeout: {e}")
```

### client.py（两种调用风格）

```python
# examples/vllm-qwen/client.py
def chat_http(base_url, model, prompt): ...    # httpx 直调
def chat_openai_sdk(base_url, model, prompt): ... # openai SDK 兼容

# CLI: --mode http|openai (default openai)
```

### benchmark.py（并发压测）

```python
async def run(base_url, model, prompt, concurrency, total):
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        tasks = [task(i) for i in range(total)]
        return await asyncio.gather(*tasks)
```

### Dockerfile.router（multi-stage）

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv export --frozen --no-dev -o requirements.txt && \
    uv pip install --system --no-cache -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY charts/ /app/charts/
COPY src/k8s_llm_runtime/ /app/src/k8s_llm_runtime/
COPY examples/vllm-qwen/server.py /app/server.py
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN apt-get update && apt-get install -y --no-install-recommends curl bash && \
    curl -fsSL https://get.helm.sh/helm-v3.14.0-linux-amd64.tar.gz | tar -xz -C /tmp && \
    mv /tmp/linux-amd64/helm /usr/local/bin/helm

EXPOSE 8080
USER 1000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
```

镜像 size 估算：~250MB。

---

## 测试策略（4 层金字塔）

```
Unit（< 30s） ─── Chart（< 30s） ─── Integration（5-8 min） ─── Manual demo
```

### Layer 1：Unit Tests

**工具**：`pytest` + `pytest-mock` + `respx`（mock httpx）

**Mock 边界**：

| 测试目标 | Mock 边界 | 工具 |
|---|---|---|
| `K8sJobOperator` | `kubernetes.client.BatchV1Api` | `MagicMock` |
| `VLLMInferenceOperator` | `subprocess.run(["helm", ...])` | `mocker.patch` |
| `ModelOperator` | 整个 `VLLMInferenceOperator` 实例 | `mocker.patch` |
| FastAPI server | `ModelOperator` 实例 | `dependency_overrides` |
| `LeaseLock` | `CoordinationV1Api` | `mocker.patch` |

### Layer 2：Chart Tests

`helm template` 渲染 → 字符串断言 + snapshot（pytest-regressions）：

```python
def test_amd_gpu_resources_rendered(helm_template):
    manifest = helm_template("./charts/llm-inference",
                             set_values=["gpu.vendor=amd", "gpu.limit=2"])
    assert "amd.com/gpu: \"2\"" in manifest
    assert "nvidia.com/gpu" not in manifest
```

### Layer 3：Integration Tests（kind cluster）

```python
@pytest.fixture(scope="session")
def kind_cluster():
    subprocess.run(["make", "cluster-up", "CLUSTER=kind"], check=True)
    yield
    subprocess.run(["make", "cluster-down", "CLUSTER=kind"], check=True)


def test_first_chat_auto_deploys_model(router_port_forward):
    r = httpx.post(f"{router_port_forward}/v1/chat/completions",
                   json={"model": "qwen-0.5b", "messages": [{"role": "user", "content": "hi"}]},
                   timeout=300)
    assert r.status_code == 200
    assert "choices" in r.json()
```

### Layer 4：Lint / Type Check

| 工具 | 范围 | CI 阶段 |
|---|---|---|
| `ruff check` + `ruff format --check` | 全部 Python | every push |
| `mypy --strict` | `src/k8s_llm_runtime/` | every push |
| `helm lint` | 全部 chart | every push |

### CI 矩阵

```yaml
# .github/workflows/ci.yml
unit-and-chart:
  runs-on: ubuntu-latest
  steps:
    - uv sync --dev
    - uv run ruff check src tests
    - uv run ruff format --check src tests
    - uv run mypy src/k8s_llm_runtime
    - uv run pytest tests/unit tests/chart --cov
    - helm lint charts/llm-inference charts/llm-router

integration:
  runs-on: ubuntu-latest
  needs: unit-and-chart
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  steps:
    - uv sync --dev
    - make cluster-up CLUSTER=kind
    - uv run pytest tests/integration -v
```

总 CI 时间：unit + chart + lint ~2 分钟；integration ~5-8 分钟（仅 main push / nightly）。

---

## 错误处理 + 可观测性

### 错误处理原则

- **类型化异常**：所有错误继承 `K8sLLMRuntimeError`，每种有独立类
- **HTTP 边界映射**：server.py 集中 exception_handler
- **瞬时错误重试**：`tenacity` 指数退避，仅 5xx/429
- **永久错误快速失败**：配置错误立即返回 400
- **不静默吞错**：全部记录（结构化字段）

### 异常 → HTTP 状态码映射

| 异常 | HTTP 状态码 | 说明 |
|---|---|---|
| `ModelNotFoundError` | 404 | 用户用未知别名 |
| `ModelAliasError` | 400 | 配置错误 |
| `VLLMDeployError` | 500 | Helm install 失败 |
| `VLLMDeployTimeoutError` | 503 | Helm install 超时 |
| `VLLMUndeployError` | 500 | Helm uninstall 失败 |
| `JobCreationError` | 500 | K8s Job 创建失败 |
| `JobTimeoutError` | 504 | Job 执行超时 |
| `LockAcquireTimeoutError` | 503 | 并发部署锁超时 |
| `K8sLLMRuntimeError` | 500 | 其他内部错误 |

### 重试策略（库内部）

```python
def _is_transient(exc):
    return isinstance(exc, ApiException) and exc.status in (429, 500, 503, 504)

@retry(stop=stop_after_attempt(5),
       wait=wait_exponential(multiplier=1, min=1, max=30),
       retry=retry_if_exception_type((ApiException, TimeoutError)) & _is_transient,
       before_sleep=before_sleep_log(logger, logging.WARNING),
       reraise=True)
def k8s_call(fn, *args, **kwargs):
    return fn(*args, **kwargs)
```

**关键**：4xx（Unauthorized / NotFound / Conflict）**不重试**。

### Helm 子进程错误处理

```python
def _run_helm(args: list[str]) -> str:
    result = subprocess.run(["helm"] + args, capture_output=True, text=True,
                            timeout=120, env={**os.environ, "KUBECONFIG": self.kubeconfig or ""})
    if result.returncode != 0:
        raise VLLMDeployError(
            f"helm {' '.join(args)} failed (rc={result.returncode}): {result.stderr}")
    return result.stdout
```

### 可观测性

#### 结构化日志

`structlog` 输出 JSON，K8s 直接采集。关键字段：
`timestamp`, `level`, `event`, `model_alias`, `namespace`, `request_id`, `latency_ms`

server.py middleware 注入 `request_id`（UUID4）。

#### Prometheus 指标

| 指标名 | 类型 | Labels |
|---|---|---|
| `k8s_jobs_created_total` | Counter | `vendor`, `result` |
| `k8s_job_duration_seconds` | Histogram | — |
| `vllm_deploy_duration_seconds` | Histogram | `model_alias` |
| `vllm_deploy_failures_total` | Counter | `model_alias`, `reason` |
| `inference_requests_total` | Counter | `model_alias`, `status` |
| `inference_latency_seconds` | Histogram | `model_alias` |
| `models_loaded` | Gauge | `model_alias` |

暴露：`/metrics` endpoint（`prometheus_client.make_asgi_app()`）；可选 ServiceMonitor 自动抓取。

#### 健康检查

| 端点 | 检查 | 失败 K8s 行为 |
|---|---|---|
| `/healthz` | 进程在跑 | 杀 Pod 重启（liveness）|
| `/readyz` | K8s API 可达 + RBAC 有效 | 摘流量（readiness）|

#### 启动时状态重建

Router 启动时 `helm list -n llm-models -o json` → 重建 `MODELS_LOADED` 指标。无外部存储依赖。

### YAGNI 边界

| 不做 | 何时再做 | 备注 |
|---|---|---|
| OpenTelemetry 分布式追踪 | v1.1（Phase 2）| 当前 structlog JSON + `request_id` 已够定位 |
| 鉴权（OAuth2 / API Key）| 上线时 | 部署在 ingress 层加 OAuth2 Proxy |
| **流式响应（SSE）** | **v1.1** | `ChatRequest.stream` 字段已预留。v1.1 加：`StreamingResponse` + `httpx.stream()` + vLLM `--enable-streaming` |
| 多模态（vLLM vision）| 模型需要时 | vLLM 0.5+ 原生支持 |
| Web UI | 不做 | FastAPI 自动 Swagger UI 已够 |

---

## 集群安装（Layer 1：scripts/cluster/）

### 双集群支持

| 集群 | 默认场景 | 理由 |
|---|---|---|
| **kind** | CI / 单元 + 集成测试 | 快、轻、无嵌套虚拟化、与 ai-flow 一致 |
| **minikube** | AMD 面试现场 demo | 跨平台、K8s 官方背书、addons 一键 |

### 统一接口（Makefile）

```makefile
CLUSTER ?= kind
KUBECONFIG ?= ./kubeconfig

cluster-up:
	@./scripts/cluster/$(CLUSTER)-up.sh

cluster-down:
	@./scripts/cluster/$(CLUSTER)-down.sh

demo: cluster-up
	./scripts/demo/deploy.sh
```

### 共享 shell 库（`scripts/cluster/common.sh`）

```bash
set -euo pipefail
export KUBECONFIG="${KUBECONFIG:-./kubeconfig}"
export CLUSTER_NAME="${CLUSTER_NAME:-k8s-llm-demo}"
log() { echo "[$(date +%H:%M:%S)] $*"; }
wait_for_node_ready() { ... }
install_ingress_nginx() { ... }
install_metrics_server() { ... }
```

### kind-config.yaml（多节点）

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

### 使用示例

```bash
make cluster-up                     # 默认 kind
make cluster-up CLUSTER=minikube    # AMD 现场
make demo                           # 部署 demo（依赖 cluster-up）
make test                           # unit + integration
```

---

## 演示流程（一图流）

```bash
# 1. 起集群
$ make cluster-up CLUSTER=kind
✓ kind cluster ready. KUBECONFIG=./kubeconfig

# 2. 部署 Router（独立步骤）
$ helm install llm-router ./charts/llm-router -n llm-system --create-namespace --wait
$ kubectl -n llm-system wait --for=condition=ready pod -l app=llm-router --timeout=120s
✓ llm-router-xxx is Ready

# 3. 端口转发（demo 阶段）
$ kubectl -n llm-system port-forward svc/llm-router 8080:8080 &

# 4. 第一次调用 → 自动部署 qwen-0.5b
$ python examples/vllm-qwen/client.py --prompt "Hello"
[Router] Model qwen-0.5b not loaded, deploying...
[Router] helm install qwen-0.5b ./charts/llm-inference ...
[Router] ✓ qwen-0.5b ready (took 67s)
[Router] Forwarding to http://qwen-0.5b.llm-models:8000/v1/chat/completions
Response: 你好！我是 Qwen...

# 5. 第二次调用 → 直接转发
$ python examples/vllm-qwen/client.py --prompt "再见"
Response: 再见！期待下次交流。

# 6. 切换模型
$ python examples/vllm-qwen/client.py --model llama-3-8b --prompt "Hi"
[Router] Model llama-3-8b not loaded, deploying...

# 7. 压测
$ python examples/vllm-qwen/benchmark.py --model qwen-0.5b --concurrency 4 --total 20

# 8. 卸载
$ curl -X DELETE http://localhost:8080/v1/models/qwen-0.5b
```

---

## 实施计划（高层）

按 6 周冲刺（与学习计划并行）：

| Week | 交付 |
|---|---|
| Week 1 | `K8sJobOperator` + types + errors + 完整单测 |
| Week 2 | `VLLMInferenceOperator` + `charts/llm-inference/` + chart tests |
| Week 3 | `ModelOperator` + `K8sLeaseLock` + `lock.py` |
| Week 4 | `examples/vllm-qwen/server.py` + `charts/llm-router/` + 集成测试 |
| Week 5 | `scripts/cluster/` + benchmark.py + CI 流水线 |
| Week 6 | 文档 + AMD 面试 demo 步骤演练 + 简历材料 |

详细每周任务分解与验证步骤由 writing-plans 技能产出独立 plan 文档。

---

## 风险与缓解

| 风险 | 缓解 |
|---|---|
| vLLM 镜像在不同 K8s 环境下启动慢 / 失败 | chart 提供 `startupProbe` + `initialDelaySeconds: 60`，CI 用 `qwen-0.5b`（小、快）|
| Helm CLI 在 Router 容器内不可用 | Dockerfile 中显式安装 helm v3.14.0 |
| 模型下载失败（HuggingFace 网络） | 支持 `model.hfTokenSecret` 配私有模型；README 提示可换镜像源 |
| 用户并发请求同模型导致并发部署 | `K8sLeaseLock`（`coordination.k8s.io/v1` Lease）|
| Router 启动时不知道已部署的模型 | `helm list -n llm-models` 启动重建 |
| AMD ROCm 集群硬件差异大 | 通过 `nodeSelector."amd\.com/gpu\.product"` 让用户显式选节点 |

---

## 不在范围内（明确排除）

- **训练 pipeline**（LoRA finetune 等）—— 用户明确选择只做推理
- **KServe / Knative 集成** —— 太重；项目自身已覆盖核心场景
- **多模态（vision / audio）** —— vLLM 0.5+ 支持，本期不做
- **GPU 共享 / MIG / MPS** —— 超出 demo 范围
- **私有模型仓库（自建 HF 镜像）** —— 文档说明，代码不集成
- **Web UI** —— FastAPI 自动 Swagger UI 已够
- **K8s Operator 框架（CRD + Controller）** —— 用户选择 Model Serving Router 而非 Operator
- **ai-flow 改造** —— 本项目不修改 ai-flow（避免范围蔓延）
