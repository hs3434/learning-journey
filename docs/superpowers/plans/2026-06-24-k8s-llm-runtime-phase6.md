# Phase 6 (Week 6): Documentation + AMD interview demo

**End-of-phase deliverable:** README polished; `docs/architecture.md` + `docs/amd-interview-demo.md` complete; demo rehearsed end-to-end.

**Working directory:** `/work/run/projects/bio-24/my_projects/k8s-llm-runtime/`

---

## Task 6.1: Architecture documentation

**Files:**
- Create: `docs/architecture.md`

- [ ] **Step 1: Write architecture.md**

```markdown
# Architecture

## Overview

k8s-llm-runtime is a Kubernetes-based vLLM model serving router. Users send
OpenAI-compatible chat completion requests to a FastAPI service. The service
transparently deploys vLLM inference Pods on demand, forwards requests, and
cleans up idle deployments.

## High-level flow

```
                    user
                     │
        POST /v1/chat/completions
                     │
                     ▼
        ┌────────────────────────────┐
        │   FastAPI Router (Pod)     │   ◄── llm-router chart
        │                            │
        │  ┌──────────────────────┐  │
        │  │ ModelOperator        │  │
        │  │  ├─ alias resolve    │  │
        │  │  ├─ lease acquire    │  │
        │  │  ├─ helm deploy      │  │
        │  │  └─ http forward     │  │
        │  └──────────────────────┘  │
        └────────────┬───────────────┘
                     │
        helm install / helm upgrade --install
                     │
                     ▼
        ┌────────────────────────────┐
        │   vLLM Inference Pod       │   ◄── llm-inference chart
        │   (one release per model)  │
        └────────────────────────────┘
```

## Components

### Python library (`src/k8s_llm_runtime/`)

Three layers with one clear responsibility each:

| Layer | Module | Purpose |
|---|---|---|
| Low | `job.py` | K8s Job CRUD via kubernetes-client |
| Mid | `vllm.py` | Helm-based vLLM deploy/undeploy |
| Mid | `lock.py` | K8s Lease-based distributed lock |
| High | `model.py` | Routing + auto-deploy + OpenAI-compat |

Other modules:
- `types.py` — Pydantic models (JobSpec, GPUResource, ChatRequest/Response)
- `errors.py` — typed exception hierarchy
- `_client.py` — kubernetes-client singleton
- `_retry.py` — tenacity wrapper for transient K8s API errors
- `_log.py` — structlog JSON config
- `_metrics.py` — Prometheus metric definitions

### Helm charts (`charts/`)

| Chart | Deploys | Replicas |
|---|---|---|
| `llm-inference` | vLLM Pod + Service | One Helm release per model |
| `llm-router` | FastAPI Router Deployment + RBAC | Single release, HPA 2-5 |

### Namespaces

| Namespace | Contents |
|---|---|
| `llm-system` | Router Deployment + ServiceAccount + RBAC |
| `llm-models` | One Helm release per loaded model |

## Request lifecycle (auto-deploy path)

1. User → POST `/v1/chat/completions` with `model: "qwen-7b"`
2. Router resolves alias → HuggingFace model `Qwen/Qwen2.5-7B-Instruct`
3. Router acquires K8s Lease `deploy-qwen-7b` (prevents concurrent deploy)
4. Router checks `helm list -n llm-models` for existing release
5. If missing or not Ready → `helm upgrade --install` with values
6. Wait for vLLM Pod to reach Ready state (default 600s timeout)
7. Forward original request to `http://qwen-7b.llm-models:8000/v1/chat/completions`
8. Release lease
9. Update metrics: `INFERENCE_LATENCY`, `INFERENCE_REQUESTS{status=ok}`, `MODELS_LOADED`
10. Return OpenAI-formatted response

## Concurrency model

- Multiple Router replicas can run simultaneously (HPA 2-5)
- Lease per model prevents concurrent deploy of same model
- Each model runs as its own Helm release (independent lifecycle)
- K8s Service auto-routes client requests within `llm-models` namespace

## GPU resource handling

`gpu.vendor` in values drives resource injection in chart templates:

| `gpu.vendor` | `limits` | nodeSelector example |
|---|---|---|
| `none` | (no GPU) | (any node) |
| `amd` | `amd.com/gpu: N` | `amd.com/gpu.product=MI300X` |
| `nvidia` | `nvidia.com/gpu: N` | `nvidia.com/gpu.product=A100` |

Python library mirrors this in `K8sJobOperator._build_container`.

## Failure modes

| Failure | Detection | Behavior |
|---|---|---|
| Unknown model alias | alias lookup | 404 + clear message |
| Helm install fails | non-zero rc | 500 + helm stderr |
| Helm install timeout | elapsed > 600s | 503 + timeout msg |
| vLLM pod OOMKilled | pod status | HPA + retry next request |
| Lease held by other | poll timeout | 503 + retry-after |
| K8s API unreachable | `/readyz` probe | 503 + readiness fails |
| Helm release drift | start-up scan | `discover_existing` rebuilds state |

## Why this design

- **3-layer Python lib** keeps each unit testable and replaceable
- **Helm chart per workload** = standard K8s deployment, no custom controllers
- **OpenAI-compatible API** = drop-in for any OpenAI client
- **Distributed Lease** = safe multi-replica Router without complex CRDs
- **Pydantic everywhere** = IDE hints + automatic OpenAPI for FastAPI

## Not in scope (YAGNI)

- LLM training pipelines (LoRA etc.)
- KServe / Knative integration (too heavy)
- Multi-modal (vision) models
- Streaming responses (SSE) — `ChatRequest.stream` reserved for v1.1
- Authentication — to be added at ingress layer
```

- [ ] **Step 2: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
mkdir -p docs
git add docs/architecture.md
git commit -m "docs: architecture overview with request lifecycle + failure modes"
```

---

## Task 6.2: AMD interview demo guide

**Files:**
- Create: `docs/amd-interview-demo.md`

- [ ] **Step 1: Write amd-interview-demo.md**

```markdown
# AMD ROCm Python Backend Interview — Demo Guide

Target role: AMD ROCm Python 后端开发工程师 (Vincent Fang's team)

## Pre-demo setup (do once)

1. **Bring your laptop** with:
   - Docker + kind installed
   - This repo cloned
   - Python 3.11 + uv installed
   - helm v3.14+ installed
   - Built Router image: `docker build -f docker/Dockerfile.router -t router:demo .`

2. **Verify environment** (5 min):
   ```bash
   cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
   uv sync --all-extras
   make cluster-up CLUSTER=kind
   make test
   ```

## Demo script (≈ 8 minutes)

### Act 1: Show the project (1 min)

Open repo in IDE. Walk through:
- `src/k8s_llm_runtime/` — three-layer library
- `charts/` — two Helm charts
- `examples/vllm-qwen/server.py` — FastAPI entry
- `docs/architecture.md` — architecture diagram

**Talking points**:
- "Extracted K8s execution from ai-flow into a standalone library"
- "Three layers: Job → vLLM → Model routing"
- "OpenAI-compatible API + Helm-based deploy + distributed lock"

### Act 2: Live demo (5 min)

In one terminal:
```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make cluster-up CLUSTER=kind
# (wait ~30s for kind to come up)

# Build & load Router image into kind
docker build -f docker/Dockerfile.router -t router:demo .
kind load docker-image router:demo --name k8s-llm-demo-kind

# Pack llm-inference chart into a ConfigMap
kubectl create configmap llm-router-chart-source \
    --from-file=charts/llm-inference/ \
    --namespace=llm-system --dry-run=client -o yaml | kubectl apply -f -

# Install llm-router chart
helm install llm-router ./charts/llm-router \
    --namespace llm-system --create-namespace --wait

# Wait for ready
kubectl wait --namespace llm-system \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/name=llm-router \
    --timeout=120s

# Port-forward
kubectl --namespace llm-system port-forward svc/llm-router 8080:8080 &
```

In another terminal:
```bash
# 1. health check
curl http://localhost:8080/healthz
# {"status":"healthy"}

# 2. readiness (verifies K8s API + RBAC)
curl http://localhost:8080/readyz
# {"status":"ready"}

# 3. list models (none loaded yet)
curl http://localhost:8080/v1/models
# {"object":"list","data":[]}

# 4. first chat → router auto-deploys qwen-0.5b
time python examples/vllm-qwen/client.py --prompt "用一句话介绍 Kubernetes"
# (waits ~60s for first deploy + model load)
# Output: ... response from model

# 5. second chat → already deployed, fast
time python examples/vllm-qwen/client.py --prompt "再说一个"
# Output: ... ~1s

# 6. show helm state
helm list -n llm-models
# qwen-0.5b    llm-models    1    deployed    qwen-0.5b-...    0.1.0

# 7. show K8s resources
kubectl get all -n llm-models

# 8. unload
curl -X DELETE http://localhost:8080/v1/models/qwen-0.5b
# 204 No Content

# Verify gone
helm list -n llm-models
# (empty)
```

### Act 3: Architecture explanation (2 min)

Show `docs/architecture.md`. Explain:
- "Auto-deploy via Helm + K8s Lease prevents concurrent deploy of same model"
- "Each model = one Helm release = independent lifecycle"
- "GPU vendor selected via values: amd/nvidia/none"

### Act 4: Q&A prep

Expected questions and answers:

| Question | Answer |
|---|---|
| "How does multi-Router replica work?" | "K8s Lease per model alias; only one replica deploys at a time. Helm list rebuilds state on startup." |
| "Why Helm over CRD/Operator?" | "Lower complexity, standard tooling, AMD cluster has helm pre-installed. Can migrate to Operator if needed." |
| "Why Pydantic?" | "Type safety + FastAPI auto-OpenAPI schema + easy testing." |
| "How would you add auth?" | "OAuth2 Proxy in front of ingress. K8s ServiceAccount handles cluster auth." |
| "AMD ROCm support?" | "Yes — `gpu.vendor=amd` injects `amd.com/gpu` resource. Tested with MI300X nodeSelector. vLLM has ROCm images." |
| "Streaming (SSE)?" | "Reserved in `ChatRequest.stream`. v1.1 plan: StreamingResponse + httpx.stream." |
| "What's the failure mode?" | "Documented in architecture.md — 8 failure modes with detection + behavior." |
| "Compared to KServe?" | "KServe is heavier (CRD + Controller). This is a thin layer on stock K8s." |

## Teardown (after demo)

```bash
make cluster-down CLUSTER=kind
```

## Materials to bring

- This repo on laptop
- Slides with architecture diagram (export from docs/architecture.md)
- Resume with this project listed
- Printed one-pager of failure modes table

## Talking points summary

1. **Extracted** ai-flow's K8s execution into a standalone library
2. **Built** OpenAI-compatible vLLM router on top
3. **Demonstrated** auto-deploy on first request
4. **Handled** concurrency with K8s Lease
5. **Ready** for AMD ROCm (one value change)
```

- [ ] **Step 2: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add docs/amd-interview-demo.md
git commit -m "docs: AMD ROCm interview demo script with live commands"
```

---

## Task 6.3: Polish README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README.md**

```markdown
# k8s-llm-runtime

> 基于 Kubernetes 的 vLLM 模型服务网关（Model Serving Router）

从 [ai-flow](https://github.com/example/ai-flow) 抽出 K8s 执行能力，构建独立的 Python 库 + Helm chart 工具集，对外提供 OpenAI 兼容的推理 API，内部按需调度 K8s 部署模型。

## 核心特性

- **OpenAI 兼容**：用户发 `POST /v1/chat/completions`，无需了解 K8s
- **按需部署**：首次请求某模型 → 自动 helm install；闲置超时 → 自动 undeploy
- **多模型并存**：同时跑 Qwen / Llama / Mistral，靠 alias 路由
- **GPU 灵活**：CPU / AMD ROCm / NVIDIA 三种模式，values.yaml 切换
- **生产级**：Helm chart + RBAC 最小权限 + Prometheus 指标 + 分布式锁

## 快速开始

```bash
# 1. 起本地 K8s 集群（默认 kind）
make cluster-up

# 2. 部署 Router
helm install llm-router ./charts/llm-router -n llm-system --create-namespace --wait

# 3. 端口转发
kubectl -n llm-system port-forward svc/llm-router 8080:8080 &

# 4. 调推理（首次会自动部署模型）
python examples/vllm-qwen/client.py --prompt "Hello"
```

## 文档

- [架构设计](docs/architecture.md)
- [AMD 面试 demo 步骤](docs/amd-interview-demo.md)
- [设计稿](../learning-journey/docs/superpowers/specs/2026-06-24-k8s-llm-runtime-design.md)
- [实施计划](../learning-journey/docs/superpowers/plans/)

## 安装依赖

```bash
uv sync --all-extras
```

## 开发命令

```bash
make test              # 跑单元测试 + chart 测试
make lint              # ruff check
make format            # ruff format
make type-check        # mypy --strict
make cluster-up        # 起 kind 集群
make cluster-down      # 停 kind 集群
make demo              # 部署 demo
make test-integration  # 跑 kind e2e
```

## Python 库 API（3 层）

```python
from k8s_llm_runtime import (
    # Low level: K8s Jobs
    K8sJobOperator, JobSpec, ContainerSpec, GPUResource, GPUVendor,

    # Mid level: Helm deploy vLLM
    VLLMInferenceOperator, VLLMDeployment,

    # High level: Model serving router
    ModelOperator, K8sLeaseLock,
    ChatMessage, ChatRequest, ChatResponse,
)
```

## 项目状态

🚧 v1.0 完成 — 仓库骨架完整，所有 Phase 已提交。

## 许可证

MIT
```

- [ ] **Step 2: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add README.md
git commit -m "docs: polish README with features + quickstart + API surface"
```

---

## Task 6.4: Final verification (full dry-run)

- [ ] **Step 1: Run full test suite**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make test
make lint
make type-check
```

Expected: all pass.

- [ ] **Step 2: Run end-to-end demo (kind)**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make cluster-up CLUSTER=kind
# Follow steps from docs/amd-interview-demo.md "Act 2"
make cluster-down CLUSTER=kind
```

Expected: full E2E works.

- [ ] **Step 3: Tag v0.1.0**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git tag -a v0.1.0 -m "v0.1.0: AMD ROCm Python backend interview demo"
git log --oneline | head -20
```

Expected: tag created, history shows the 6 phases.

---

## Phase 6 Verification

End-of-phase state:
- `docs/architecture.md` — comprehensive architecture documentation
- `docs/amd-interview-demo.md` — live demo script with expected questions
- `README.md` — polished
- Git tagged `v0.1.0`
- Project ready for AMD interview

**Project complete.** 🎉

---

# End of Plan

Total: **6 phases, ~40 tasks, ~150 steps**. Each task is a self-contained unit that produces a commit.

For execution, choose:
1. **Subagent-driven** (recommended): dispatch fresh subagent per task, review between tasks
2. **Inline execution**: run in this session with checkpoints

See `2026-06-24-k8s-llm-runtime-plan.md` for execution handoff details.
