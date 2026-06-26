# 胡盛

- 电话：188-5665-3017
- 邮箱：hs3434@foxmail.com
- 个人网站：[hs3434.github.io](https://hs3434.github.io)
- **求职意向**：AMD ROCm Python 后端开发工程师（ROCm Radeon Cloud 方向）

---

## 个人简介

3 年生物信息工程化经验，自学转型 K8s 后端栈。
**容器化部署、资源调度、任务编排、GPU 推理服务**。
最近 1 周自学 K8s / Helm，独立完成 [**k8s-llm-runtime**](https://github.com/hs3434/k8s-llm-runtime)（K8s 上的 vLLM 模型服务网关），**v0.1.0 tagged，可现场跑 demo**。
熟悉 Snakemake 类 Workflows 的 ML 平台抽象。

## 技术博客

- [Transformer 从入门到上手](https://hs3434.github.io/2025/03/03/transformer1/)
- [GPT 风格 Transformer 解码 EEG：为什么、怎么做、踩了什么坑](https://hs3434.github.io/2025/06/08/transformer-eeg-decoding/)
- [从零搭一套端到端 EEG 信号处理工具链](https://hs3434.github.io/2025/06/08/eeg-signal-processing-toolchain/)

---

## 求职技能（按岗位匹配排序）

| 类别 | 技能 |
|------|------|
| **后端核心** | Python 3.11+、FastAPI、pytest |
| **容器与编排** | Docker、Kubernetes、Helm、镜像仓库管理 |
| **GPU / LLM 生态** | vLLM、PyTorch、Hugging Face |
| **工具链** | uv、mypy、GitHub Actions |
| **运维** | Linux 运维 |
| **数据库** | PostgreSQL、MySQL、Redis |

---

## 项目经验

### k8s-llm-runtime：K8s 上的 vLLM 模型服务网关 - 自学demo项目

**问题**（对应 JD 职责 1 + 3）：vLLM 模型部署需 GPU + 容器 + 路由，团队多人共享时模型管理复杂；研究/小团队想用 OpenAI 兼容 API 时门槛高。
（直接对应 JD："大模型训练/推理 Workshop、教程、功能演示"）

### 架构（双 chart + 三层 lib + 镜像优化）

- `charts/llm-inference/`：vLLM 负载 chart，**GPU vendor 切换仅靠 `values.yaml`**
  （amd.com/gpu / nvidia.com/gpu / none 三态，values 显式选择）
- `charts/llm-router/`：FastAPI 网关 chart
  - RBAC 最小权限（Pod/Service/ConfigMap read+write + Lease）
- `src/k8s_llm_runtime/`：3 层 lib 抽象
  - `K8sJobOperator`（低层，通用 Job 调度）
  - `VLLMInferenceOperator`（中层，helm CLI subprocess + GPU vendor）
  - `ModelOperator`（高层，OpenAI 兼容 + 自动部署）

### 4 大技术亮点

1. **lib 三层分层抽象**（对应 JD 后端架构能力）
   - 上层 ModelOperator 只关心 load_model(alias) / unload_model(alias)
   - 中层 VLLMInferenceOperator 封装 helm 细节
   - 低层 K8sJobOperator 通用 K8s Job 调度
2. **Helm ConfigMap 注入 aliases**（对应 JD 容器化 + 资源调度）
   - 避免每次新增模型都 rebuild 镜像（GPU 镜像 15-20GB rebuild 5-10min）
   - ConfigMap 秒级生效，零镜像重建
3. **K8s Lease 分布式锁**（对应 JD 集群运维 + HA）
   - coordination.k8s.io/v1 Lease 防止 Router 多副本并发部署同一模型
   - 锁粒度按 model alias，自动过期 + 续约
4. **业务级 Prometheus metrics**（对应 JD 平台可观测性）
   - `chat_completions_duration_seconds`（histogram，含 status code 标签）
   - `http_requests_total`（counter，按 method/route/status）
   - `models_loaded`（gauge，反映 in-memory state）

### GPU vendor 切换 demo（对应 JD 加分 GPU 集群）
- values.yaml `gpu.vendor=amd|nvidia|none`
- AMD：amd.com/gpu 资源调度，ROCm vLLM 镜像
- NVIDIA：nvidia.com/gpu 资源调度，CUDA vLLM 镜像
- none：CPU only 模式（kind cluster 默认，本地开发用）

### 质量保证
- 31 commits / 90 tests pass / coverage 88%
- ruff + mypy strict + helm-lint 全 clean
- 2 Helm charts（llm-inference + llm-router）

### 踩坑与修复
- kind 节点国内镜像加速：containerdConfigPatches + DaoCloud mirror

### 基于 Snakemake 的 ML 平台工作流框架（生信背景）

- 背景：Snakemake rule 语法无法实现模块随意组合
- 设计：摈弃 rule 语法，直接调内部接口动态生成 rule，规范输入输出类型即可积木式拼接
- 关联：JD 加分项"机器学习平台研发经验"——本项目是 ML 平台抽象的工程实践
- **详细博客**：[不满 Snakemake 的静态 rule？我用 Python 对象动态构建了一条 RNA-seq 流水线](https://hs3434.github.io/2025/06/08/rnaseq-pipeline-engineering/)

### 脑机接口 CNN 解码器（PyTorch）—— 自学的demo项目

- 端到端时空卷积解码 EEG 信号
- PyQt 实时 GUI + FastAPI 暴露
- **仓库**：[github.com/hs3434/bci-pipeline-demo](https://github.com/hs3434/bci-pipeline-demo)

---

## 工作经历

### 上海尤里卡信息科技有限公司 ｜ 生物信息工程师 ｜ 2025.04 - 至今

- **rnaseq**（项目主力）：基于 Snakemake 的 RNA-seq 自动化分析 pipeline，Docker / Apptainer 容器化，20 核并行；config.yaml 驱动配置；公司业务自动化主线
- **helix**（Python 后端 API）：FastAPI + Click + Pydantic v2 实现的生物信息 API 服务，给 rnaseq pipeline 提供结果展示层；类型化 + 测试覆盖
- **服务端运维**：Linux 服务器日常维护，Nginx 反向代理，systemd 服务管理

### 上海欧易生物医学科技有限公司 ｜ 生物信息研发工程师 ｜ 2022.08 - 2024.07

- **云平台生信工具开发**：R / Python / Linux / Docker / 云原生
- **业务自动化**：医学转录组业务流程自动化，模块化、可复用
- **平台地址**：[cloud.oebiotech.com](https://cloud.oebiotech.com/#/home)

### 上海欧易生物医学有限公司 ｜ 生物信息实习生 ｜ 2021.10 - 2022.01

- 单细胞转录组：质控、常规分析、售后、个性化分析
- 主要技术：单细胞转录组、R、Python、Linux

---

## 教育背景

**西北农林科技大学** ｜ 植物科学与技术专业 ｜ 本科 ｜ 2018.09 - 2022.07 ｜ GPA：3.35

- 毕业论文：《基于逻辑斯蒂回归确定小麦倒伏相关性状及抗倒性状指标》
- 大创项目：根瘤菌接种对紫花苜蓿抗铜污染的影响（参与作者）

---

## 个人优势

- **1 周自学 K8s 后端栈**：从零到 v0.1.0 tagged 项目，独立完成双 Helm chart + Python lib
- **现场 demo 能力**：可自带电脑在 kind cluster 上跑通完整 LLM 推理流程（部署 → 路由 → chat completions → metrics）
- **学习能力强**：自学生物信息、算法、K8s 等多领域知识，独立完成项目
- **3 年 Python 工程化经验**：从科研脚本到云平台工具的完整路径