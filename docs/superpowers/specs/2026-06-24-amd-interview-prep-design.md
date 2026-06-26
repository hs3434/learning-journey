# AMD ROCm 岗面试准备 — 设计稿

**日期**：2026-06-24
**状态**：待审阅
**目标**：为 AMD ROCm Python 后端岗面试准备两套简历（通用 + 路线专用）+ k8s-llm-runtime 项目的 1-pager / 5min pitch / 白板 Q&A / 架构图，共 8 个产出文件 + 1 个 spec。

> **范围**：本 spec 覆盖"从已有学习材料到可投岗、可面试"的完整产出物。**k8s-llm-runtime 仓库本身不修改**——它是面试项目的代码载体，本 spec 围绕"如何呈现"它。

---

## 背景与目标

### 起源

学习仓库 learning-journey 下已沉淀两条完整学习路线的产出物：

- **brain-computer-interface 路线**（已学完）：含 BCI 软件项目、PyQt GUI、CNN 解码器；现有 `notes/resume.md` (7.7KB) + `resume.pdf` (130KB) + `interview-prep-plan.md` (9.3KB) + `interview-prep.md` (6.4KB)
- **amd-rocm-python-backend 路线**（进行中）：含 k8s-llm-runtime 完整项目（31 commits, v0.1.0 tagged）；但 notes/ 下只有 `job-requirements.md`（3KB），**没有简历、没有面试弹药**

通用 `notes/Resume.md`（59 行）当前状态：
- 求职意向未写
- 项目经验只 3 个：Snakemake 框架、Linux 系统维护、PyTorch
- 技能栏无 Docker / k8s / Helm / FastAPI / Prometheus
- 无 BCI 项目、无 k8s-llm-runtime 项目

### 目标

补齐"投 AMD ROCm Python 后端岗"所需的全部产出物：

1. **两套简历**：通用简历（多向）+ amd-rocm 路线专用简历（单向上深度）
2. **项目展示**：k8s-llm-runtime 项目 1-pager + 5min pitch + 白板 Q&A + 架构图
3. **可立即投岗**：PDF 导出，链接可挂

### 适配 JD 关键需求

参考 `tracks/amd-rocm-python-backend/notes/job-requirements.md`：

| JD 要求 | 本 spec 对应物 |
|---|---|
| Python 后端 2 年+ | 通用 Resume.md 强化 Python / 异步 / FastAPI 技能栏 |
| Docker / k8s / Helm 部署 | amd-rocm 简历突出 K8s 抽象 / Helm chart / ConfigMap 注入 |
| 容器化、任务编排、集群运维 | k8s-llm-runtime 1-pager 第 2、3 亮点 |
| AMD ROCm 加分 | amd-rocm 简历强化 ROCm / vLLM 关键词；Q&A 5 题 |
| 大模型推理 Workshop | 5min pitch（向面试官讲项目的口径） |

---

## 关键决策汇总

| 维度 | 决策 | 理由 |
|---|---|---|
| 简历版本策略 | **两套：通用 + amd-rocm 专用** | 通用应对多向投递；专用强化 AMD 关键词 |
| 通用 Resume.md 变化 | 加 2 个项目卡片（k8s-llm-runtime 主力 + BCI 轻提） | 用户已学完 BCI，应反映在通用简历 |
| amd-rocm 专用 | 完全新建（沿用 BCI `resume.md` 模板） | BCI 模板 7.7KB 已成熟，复用结构 |
| 1-pager 风格 | **技术架构型**（4 大亮点） | 适配技术面试（非量化型 / 非踩坑型） |
| 执行节奏 | **Approach 2 一次性**（不分阶段） | 用户选择，3-5h 一次产出 |
| 博客 | **不在本 spec 范围**（v0.2.0 可选） | 1-pager 是博客的素材源；v0.2.0 再扩写 |
| 架构图格式 | Mermaid（.mmd） | GitHub/VSCode/1-pager 内联渲染 |
| PDF 导出工具 | weasyprint（BCI 已用）| 复用 BCI `resume.css` 样式 |

---

## 文件清单（8 个产出 + 1 个 spec）

```
/work/run/projects/bio-24/my_projects/learning-journey/
├── notes/
│   └── Resume.md                                          # ① 修改（+2 卡片）
├── tracks/amd-rocm-python-backend/
│   └── notes/
│       ├── job-requirements.md                            # 已有（不修改）
│       ├── resume.md                                      # ② 新建
│       ├── resume.css                                     # ③ 新建（从 BCI 复制）
│       ├── resume.pdf                                     # ④ 新建（weasyprint 导出）
│       └── k8s-llm-runtime/
│           ├── 1-pager.md                                 # ⑤ 新建
│           ├── 5min-pitch.md                              # ⑥ 新建
│           ├── whiteboard-qa.md                           # ⑦ 新建
│           └── architecture.mmd                           # ⑧ 新建
└── docs/superpowers/specs/
    └── 2026-06-24-amd-interview-prep-design.md            # 本文档
```

---

## ① 通用 Resume.md 修改

### 修改前状态
- 项目经验 3 个：Snakemake、Linux 维护、PyTorch
- 求职意向未写
- 技能：C/C++/VB/R/Python/Matlab/SAS + Linux/PyTorch/Office

### 修改后状态
- 求职意向新增 1 行：`**求职意向**：Python 后端 / K8s / 生信工程`
- 项目经验 5 个：保留 3 + 新增 2
- 技能栏扩展

### 新增项目卡片 1：k8s-llm-runtime（6-8 行）

```markdown
### k8s-llm-runtime：OpenAI 兼容的 K8s vLLM 模型服务网关

- **背景**：vLLM 模型部署需 GPU + 容器 + 路由，团队多人共享时模型管理复杂
- **设计**：用 Helm chart + Python lib 抽象，让"加载/卸载模型"成为一行命令
- **实现**：双 chart（llm-inference + llm-router）+ lib 三层（K8sJobOperator / VLLMInferenceOperator / ModelOperator）
- **关键决策**：K8s Lease 分布式锁防 Router 多副本并发部署；ConfigMap 注入 aliases 避免镜像 rebuild
- **可观测性**：Prometheus 业务级 metrics（`chat_completions_duration_seconds` 等）+ structlog JSON 日志
- **质量**：31 commits / 90 tests pass / coverage 88% / ruff + mypy strict + helm-lint clean
- **仓库**：[github.com/.../k8s-llm-runtime](https://...)  ·  v0.1.0 tagged
```

### 新增项目卡片 2：BCI 软件项目（3-4 行）

```markdown
### 脑机接口实时信号处理与解码软件

- 6 周学习路线产出：PyQt 实时 GUI + CNN 时空解码器（PyTorch，可选）
- 模块化信号处理 pipeline（滤波 / ICA / 时频），服务端 FastAPI 暴露
- 详见 `tracks/brain-computer-interface/notes/resume.md`
```

### 技能栏扩展

新增项：**容器 / 平台**：Docker, k8s, Helm, Prometheus, Grafana · **Web 后端**：FastAPI, Pydantic, async/await, httpx

### 验证
- 通用 Resume.md 长度 ≤ 1.5 页
- 求职意向首屏可见
- 5 个项目倒序（k8s-llm-runtime 最新在最上）

---

## ② amd-rocm 专用 resume.md（新建）

### 整体策略
完全沿用 BCI `resume.md` 结构（7.7KB 模板已成熟），但内容替换为 AMD ROCm Python 后端工程师方向。

### 结构
```markdown
# 胡盛

- 电话：188-5665-3017
- 邮箱：hs3434@foxmail.com
- 个人网站：hs3434.github.io
- 求职意向：**AMD ROCm Python 后端工程师**

---

## 个人简介

3 年生物信息工程化经验 + 自学 K8s 后端栈。
专注**容器化部署、任务编排、GPU 推理服务网关**。
熟悉 Python 异步、FastAPI、Helm、Prometheus、vLLM/ROCm。

---

## 求职技能（按岗位匹配排序）

| 类别 | 技能 |
|------|------|
| 后端 | Python（asyncio, type hints）, FastAPI, Pydantic, httpx |
| 容器/平台 | Docker（multi-stage）, Kubernetes（Pod/Service/Deployment/RBAC）, Helm chart |
| 推理/ML | vLLM, ROCm（HSA/ROCk）, PyTorch（CNN 时空解码器） |
| 可观测性 | Prometheus（prometheus_client）, structlog, Grafana |
| 工具链 | uv, ruff, mypy, pytest, GitHub Actions |
| 生信（背景） | Snakemake, R, Linux 服务端 |

## 项目经验

### k8s-llm-runtime：K8s 上的 vLLM 模型服务网关

[深度展开 8-12 行，强调 4 大技术亮点：分层抽象 / Helm ConfigMap 注入 / K8s Lease 锁 / Prometheus 业务 metrics]

### 脑机接口 CNN 解码器（PyTorch）

[2 行轻提：端到端时空卷积解码，详见 BCI 专用简历]

### 基于 Snakemake 的生信工作流框架

[2 行：动态 rule 生成的工程化抽象]

## 工作经历

[欧易 + 尤里卡，突出"云平台 / 自动化 Pipeline / Docker 部署 / 服务器运维"]

## 教育背景

[沿用通用]

## 优势

[沿用通用 + 1 行"K8s 后端栈可立即上手 GPU 推理服务方向"]
```

### 关键内容：k8s-llm-runtime 深度展开

```markdown
**问题**：vLLM 模型部署需 GPU + 容器 + 路由，研究/小团队想用 OpenAI 兼容 API 时门槛高

**架构**：双 chart + 三层 lib
- `charts/llm-inference/`：vLLM 负载 chart，GPU vendor 切换仅靠 `values.yaml`
- `charts/llm-router/`：FastAPI 网关，ConfigMap 注入 initContainer 加载兄弟 chart
- `src/k8s_llm_runtime/`：3 层 lib 抽象（K8sJobOperator → VLLMInferenceOperator → ModelOperator）

**4 大技术亮点**：
1. **分层抽象**：上层 ModelOperator 只关心"加载/卸载模型"；底层 Helm 细节封装在 VLLMInferenceOperator
2. **Helm ConfigMap 注入**：aliases 通过 ConfigMap 动态注入，**避免每次新增模型都 rebuild 镜像**
3. **K8s Lease 分布式锁**：`coordination.k8s.io/v1` Lease 防止 Router 多副本并发部署同一模型
4. **业务级 Prometheus metrics**：`chat_completions_duration_seconds` / `http_requests_total` / `models_loaded`

**质量保证**：31 commits / 90 tests pass / coverage 88% / ruff + mypy strict + helm-lint clean
**踩坑**：Service DNS 不匹配 bug（`--set fullnameOverride={release_name}` 修复） + 国内 kind 节点镜像加速（DaoCloud mirror）

**未来**：SSE 流式推理 v1.1 / RBAC 收紧只读 / 真实 GPU 集群 e2e
```

### 验证
- amd-rocm 专用 resume.md 长度 1.5-2 页
- 求职意向 / 个人简介 / 技能栏三段都是"AMD ROCm 关键词强相关"
- k8s-llm-runtime 占用 1/3 篇幅

---

## ③ ④ resume.css + resume.pdf

### resume.css
- **来源**：从 `tracks/brain-computer-interface/notes/resume.css`（1KB）复制
- **修改**：不修改（样式通用，简历内容差异由 .md 决定）

### resume.pdf
- **工具**：weasyprint（apt 装过；如未装则用 wkhtmltopdf 替代）
- **命令**：
  ```bash
  cd tracks/amd-rocm-python-backend/notes
  weasyprint resume.md resume.pdf --stylesheet resume.css
  ```
- **导出后验证**：PDF 1.5-2 页，求职意向首屏可见，技能表格渲染正确

---

## ⑤ k8s-llm-runtime/1-pager.md（技术架构型）

### 结构（1.5 页内）

```markdown
# k8s-llm-runtime
## OpenAI 兼容的 K8s vLLM 模型服务网关

> 1 行定位：用 Helm + Python lib 把 vLLM 模型部署变成一行命令，自动暴露 OpenAI 兼容 API。

## 问题

vLLM 模型部署需要 GPU + 容器 + 路由，团队多人共享时模型管理复杂；
研究/小团队想用 OpenAI 兼容 API 时门槛高，每次新模型都要重写 K8s manifest。

## 架构（一张 Mermaid 图）

[内联 `architecture.mmd` 内容]

## 4 大技术亮点

### 1. lib 三层分层抽象
- `K8sJobOperator`（最底）：通用 K8s Job 调度
- `VLLMInferenceOperator`（中）：封装 helm install/upgrade/uninstall + GPU vendor 切换
- `ModelOperator`（高）：用户只调 `load_model(alias)` / `unload_model(alias)`，底层细节全封装

### 2. Helm ConfigMap 注入 aliases
- vLLM 镜像内已有 `aliases.json` 模板，**只需 ConfigMap 注入**而非 rebuild 镜像
- initContainer 把 chart 源从 ConfigMap cp 到 `/app/charts/llm-inference/`
- 新增模型仅改 ConfigMap，零镜像重建

### 3. K8s Lease 分布式锁
- 用 `coordination.k8s.io/v1` Lease 防 Router 多副本并发部署同一模型
- 锁粒度按 model alias，自动过期 + 续约

### 4. 业务级 Prometheus metrics
- `chat_completions_duration_seconds`（histogram，含 status code 标签）
- `http_requests_total`（counter，按 method/route/status）
- `models_loaded`（gauge，反映 in-memory state）
- 直接进 Grafana，业务可观测性强

## 量化指标

| 维度 | 数值 |
|---|---|
| Commits | 31 |
| Tests | 90 pass |
| Coverage | 88% |
| Lint | ruff + mypy strict + helm-lint 全 clean |
| Helm charts | 2（llm-inference + llm-router） |

## 未来工作

- v1.1：SSE 流式推理（`ChatRequest.stream` 字段已预留）
- v1.1：RBAC 收紧只读 services
- v1.1：真实 GPU 集群 e2e（M3 MacBook 无 GPU，仅 CI kind 跑过）
```

---

## ⑥ k8s-llm-runtime/5min-pitch.md

### 结构（5 段，每段标注时长）

```markdown
# 5 分钟面试讲解稿 — k8s-llm-runtime

## 0:00 - 0:30  开场（30 秒）

> "我是胡盛，3 年生物信息工程化经验。最近自学 K8s 后端栈，做了 k8s-llm-runtime —— 一个在 K8s 上把 vLLM 模型部署变成一行命令的项目，暴露 OpenAI 兼容 API。今天用 5 分钟讲一下。"

## 0:30 - 2:00  问题陈述（90 秒）

- vLLM 模型部署需要 GPU + 容器 + Service 路由 + 配置管理
- 团队多人共享 GPU 资源时：谁部署了哪个模型、版本多少、怎么下线？
- 现有方案（裸 YAML / KServe）门槛高或者引入 CRD 复杂度
- 我的目标：**用户发 `POST /v1/chat/completions`，网关在后台按需 `helm install` 部署对应模型，部署完成后自动转发**

## 2:00 - 4:00  架构 + 4 大亮点（120 秒）

**架构**（30 秒）：双 chart（llm-inference + llm-router）+ 三层 Python lib

**4 大亮点**（90 秒，每点 ~22 秒）：
1. **分层抽象** — ModelOperator 只关心 load/unload，Helm 细节全封装
2. **ConfigMap 注入 aliases** — 新模型不改镜像，仅改 ConfigMap
3. **K8s Lease 锁** — Router 多副本防并发部署同模型
4. **业务级 metrics** — `chat_completions_duration_seconds` 等可直接进 Grafana

## 4:00 - 4:30  量化 + 1 个踩坑（30 秒）

- 量化：31 commits / 90 tests / coverage 88% / lint 全 clean
- 踩坑：Service DNS 不匹配 bug，原因是 helm install 生成的 Service name 带 release 前缀，get_endpoint 拼的是无前缀名。修：`--set fullnameOverride={release_name}`。这个 bug 教会我 K8s 命名空间内 DNS 是 FQDN

## 4:30 - 5:00  收尾（30 秒）

- 仓库独立维护，v0.1.0 tagged
- 未来 v1.1 计划：SSE 流式、RBAC 收紧、真实 GPU 集群 e2e
- 演示 / 提问环节
```

---

## ⑦ k8s-llm-runtime/whiteboard-qa.md（30 题）

### 主题分布

| 主题 | 题数 |
|------|------|
| 架构决策 | 10 |
| 故障处理 / 可观测性 | 5 |
| 性能优化 | 5 |
| K8s 细节 | 5 |
| AMD / ROCm | 5 |

### 架构决策（10 题样例）

1. 为什么不直接用 KServe / vLLM Operator？
   - KServe 引入 CRD 复杂度，AMD ROCm 集群支持有限；本项目追求"用 K8s 原生资源 + Helm 解决"
2. 为什么不直接用 vLLM OpenAI Server 镜像？
   - 直接用缺乏多模型管理、metrics 暴露、租户隔离；本项目加 Router 解决
3. 为什么 Router 仅 K8s 内运行（不开本地模式）？
   - in-cluster config 自动认证；本地模式需 kubeconfig 路径，部署摩擦
4. lib 三层（K8sJobOperator / VLLMInferenceOperator / ModelOperator）分层的依据？
   - K8sJobOperator 通用（任何 Job 都能用），VLLMInferenceOperator 专用 vLLM 部署，ModelOperator 是用户面
5. Helm CLI subprocess 而非 python-helm 库？
   - python-helm 久未更新；CLI 是事实标准；错误码稳定
6. ConfigMap 注入 aliases 替代 rebuild 镜像的依据？
   - rebuild 一次 5-10 分钟（GPU 镜像大）；ConfigMap 秒级生效
7. K8s Lease 而非 CRD 实现分布式锁的依据？
   - Lease 是 K8s 原生，CRD 引入 etcd 写入压力
8. GPU vendor 通过 values.yaml 显式选择（amd/nvidia/none）？
   - chart 不能在 install 时探测集群；显式优于隐式
9. Chart 拆分（llm-inference + llm-router）vs 单 chart？
   - 拆分利于 llm-inference 单独被消费；Router 复用 ConfigMap 注入
10. 错误处理用类型化异常 + tenacity 重试 + HTTP 状态码映射的边界？
    - 库抛类型化异常；服务捕获后映射 HTTP 4xx/5xx；tenacity 处理 transient 错误（K8s API 503 / network）

### 故障处理 / 可观测性（5 题样例）

1. vLLM Pod 挂掉怎么发现？
   - liveness probe + Prometheus `kube_pod_container_status_running` 指标 + Router 5xx rate 告警
2. helm install 失败（如镜像拉取超时）怎么反馈给用户？
   - 类型化异常 `HelmInstallError` → HTTP 503 + retry-after header
3. Router 多副本下，一个副本挂掉会影响请求吗？
   - 不会，Service 负载均衡；Lease 锁仅保护 helm 操作
4. vLLM 启动慢（30-60s），Router 怎么避免把请求转给未就绪的 Pod？
   - readiness probe + 启动期间请求返回 503 retry-after
5. Prometheus metrics 抓取失败，Router 还能用吗？
   - 完全解耦；metrics 仅 observability，缺失不影响功能

### 性能优化（5 题样例）

1. Router 延迟瓶颈在哪？
   - 主要是 K8s API 调用（lease / helm status）；vLLM 推理本身是 GPU 瓶颈
2. ConfigMap 注入的 aliases 有大小限制吗？
   - 1MB（etcd 限制）；aliases 通常 KB 级，安全
3. vLLM 推理请求走 HTTP/1.1 还是 HTTP/2？
   - httpx 客户端 HTTP/1.1；HTTP/2 优化空间大
4. Helm 操作能并行吗？
   - 同模型不能并行（Lease 锁）；不同模型可并行
5. 启动时如何快速恢复 in-memory 状态（models_loaded）？
   - lifespan 中 `discover_existing()` 调 K8s API 列已部署 release，rebuild 状态；try/except 包裹

### K8s 细节（5 题样例）

1. Helm values 怎么合并多文件？
   - helm install `-f base.yaml -f override.yaml`，后覆盖前
2. Service DNS 在 K8s 内怎么解析？
   - `{service}.{namespace}.svc.cluster.local`；helm fullnameOverride 改了 service name
3. Lease 锁的租约（lease duration）和续约周期怎么设？
   - duration 30s，renew 10s（1/3）；超时自动释放
4. RBAC 最小权限是什么？
   - Pod/Service/ConfigMap read+write + Lease + Helm（subprocess 不需 K8s RBAC）
5. kind 集群和 minikube 部署差异？
   - kind 节点内是 containerd；minikube 取决于 driver；本项目 CI 默认 kind

### AMD / ROCm（5 题样例）

1. vLLM 在 ROCm 和 CUDA 上差异？
   - API 几乎一致；底层 ROCm vs CUDA；HIP 兼容层；性能差距通常 5-15%
2. amd.com/gpu 资源调度和 nvidia.com/gpu 区别？
   - K8s 设备插件不同；values.yaml 显式 `gpu.vendor=amd|nvidia` 切换
3. ROCm 镜像（如 rocm/pytorch）有多大？
   - base 镜像 ~5-10GB；vLLM ROCm 镜像 ~15-20GB；pull 时间长
4. 怎么在没 AMD GPU 的机器上开发？
   - kind 集群 + GPU vendor=none；ROCm 真机需 ROCm-enabled 节点
5. AMD ROCm 集群上的 vLLM 性能调优？
   - HSA 内存预分配、batch size 调优、HCC vs ROCr runtime 选择

---

## ⑧ k8s-llm-runtime/architecture.mmd

```mermaid
graph TB
    User[用户 / 应用]
    Router[Router<br/>FastAPI + uvicorn]
    ModelOp[ModelOperator<br/>load/unload]
    VLLMOp[VLLMInferenceOperator<br/>helm install/upgrade]
    K8sOp[K8sJobOperator<br/>低层 K8s API]
    Helm[helm CLI]
    Lease[(K8s Lease<br/>coordination.k8s.io)]
    K8sAPI[(K8s API Server)]
    VLLMPod[vLLM Pod<br/>GPU]
    Prom[Prometheus]
    Grafana[Grafana]

    User -->|POST /v1/chat/completions| Router
    Router --> ModelOp
    ModelOp --> VLLMOp
    VLLMOp --> K8sOp
    VLLMOp -->|acquire/release| Lease
    VLLMOp -->|helm install/upgrade/uninstall| Helm
    Helm --> K8sAPI
    K8sOp --> K8sAPI
    K8sAPI --> VLLMPod
    Router -->|HTTP forward| VLLMPod
    Router -->|expose| Prom
    Prom --> Grafana

    style Router fill:#f9f,stroke:#333
    style VLLMPod fill:#bbf,stroke:#333
```

---

## 验证标准（Definition of Done）

### 通用 Resume.md
- [ ] 文件长度 ≤ 90 行
- [ ] 求职意向首屏可见
- [ ] 5 个项目（k8s-llm-runtime 排第一）
- [ ] 技能栏含 Docker / k8s / Helm / FastAPI / Prometheus

### amd-rocm 专用 resume.md
- [ ] 文件长度 100-150 行
- [ ] 求职意向 "AMD ROCm Python 后端工程师"
- [ ] k8s-llm-runtime 占用 ≥ 1/3 篇幅
- [ ] 4 大技术亮点全部体现
- [ ] 关键词：AMD ROCm / vLLM / Helm / RBAC 至少各出现 1 次

### resume.pdf
- [ ] 1.5-2 页
- [ ] weasyprint 命令成功无 error
- [ ] 表格 / 列表渲染正确
- [ ] 与 BCI resume.pdf 排版风格一致

### 1-pager.md
- [ ] ≤ 1.5 页（80 列宽）
- [ ] 1 行定位
- [ ] 4 大亮点每点 4-6 行
- [ ] Mermaid 图内联（不依赖外部文件）
- [ ] 量化指标表

### 5min-pitch.md
- [ ] 5 段时间标注（0:00-0:30 / 0:30-2:00 / 2:00-4:00 / 4:00-4:30 / 4:30-5:00）
- [ ] 实际朗读计时 4:30-5:00
- [ ] 含 1 个踩坑故事（DNS bug）

### whiteboard-qa.md
- [ ] 30 题齐全
- [ ] 主题分布符合（10+5+5+5+5）
- [ ] 每题答案 1-3 句要点
- [ ] AMD / ROCm 5 题必有

### architecture.mmd
- [ ] Mermaid 语法正确（GitHub 渲染 OK）
- [ ] 包含：用户 / Router / lib 三层 / Lease / vLLM Pod / Prometheus
- [ ] 1-pager.md 内联渲染成功

### 整体
- [ ] 所有 8 个产出文件 commit 到 learning-journey main 分支
- [ ] 本 spec commit 到 learning-journey main 分支
- [ ] 无 "TBD / TODO / 略 / 待补充" 标记

---

## 时间估计

| 任务 | 估计 |
|---|---|
| ① 通用 Resume.md 修改 | 30 min |
| ② amd-rocm 专用 resume.md | 1.5 h |
| ③ ④ resume.css / .pdf | 15 min |
| ⑤ 1-pager.md | 1 h |
| ⑥ 5min-pitch.md | 30 min |
| ⑦ whiteboard-qa.md（30 题） | 1.5 h |
| ⑧ architecture.mmd | 15 min |
| 验证 + 调整 + commit | 30 min |
| **总计** | **~5 h** |

---

## 参考资源

### 现有材料（直接复用）
- `tracks/brain-computer-interface/notes/resume.md`：模板（7.7KB）
- `tracks/brain-computer-interface/notes/resume.css`：样式（1KB）
- `k8s-llm-runtime/docs/architecture.md`：1-pager 素材
- `k8s-llm-runtime/docs/amd-interview-demo.md`：1-pager 素材
- `k8s-llm-runtime/README.md`：项目卡片基础信息

### 不在本 spec 范围（v0.2.0 考虑）
- 公开博客（基于 1-pager 扩写）
- 简历英文版（海外投岗）
- 视频 demo（架构图升级）
- STAR 故事库（行为面准备）

---

## Open Questions（用户已确认）

- ✅ 范围：L1 简历 + L2 项目展示
- ✅ 简历策略：两套（通用 + amd-rocm 专用）
- ✅ 通用 Resume.md：加 2 卡片（k8s-llm-runtime 主力 + BCI 轻提）
- ✅ 1-pager 风格：技术架构型
- ✅ 执行节奏：Approach 2 一次性
- ✅ 博客：v0.2.0 可选
- ✅ 架构图：Mermaid
- ✅ PDF 工具：weasyprint
