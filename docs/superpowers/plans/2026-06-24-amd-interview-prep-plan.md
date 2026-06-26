# AMD ROCm 面试准备 — 阶段 1（简历）实施 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 AMD ROCm Python 后端岗投岗准备两套简历（通用 + amd-rocm 专用）+ 导出 PDF。简历立即可用，先于 1-pager / 5min-pitch / Q&A / 架构图（阶段 2 v0.2.0 后续）。

**Architecture:**
- 通用 `notes/Resume.md` 走"多向投递"路径，求职意向 3 向 + 5 项目（k8s-llm-runtime 主力 + BCI 轻提 + 3 个原有）
- amd-rocm 专用 `tracks/amd-rocm-python-backend/notes/resume.md` 按 JD 定制（job-requirements.md 5 硬性 + 9 加分），4 层技能栏 + 现场 demo 能力显式
- 复用 BCI 路线的 `resume.css` 样式，weasyprint 导出 PDF

**Tech Stack:**
- Markdown 写作（resume 内容）
- weasyprint（PDF 导出，复用 BCI css）
- Bash（cp / git）
- 关键词自检：grep

**Spec:** `docs/superpowers/specs/2026-06-24-amd-interview-prep-design.md`（commit `6bbd213`）

---

## 任务总览

| Task | 文件 | 状态 |
|---|---|---|
| 1 | `tracks/amd-rocm-python-backend/notes/resume.css` (cp from BCI) | 必做 |
| 2 | `notes/Resume.md` (modify) | 必做 |
| 3 | `tracks/amd-rocm-python-backend/notes/resume.md` (create) | 必做 |
| 4 | `tracks/amd-rocm-python-backend/notes/resume.pdf` (weasyprint) | 必做 |
| 5 | 整体验证（DoD 自检） | 必做 |
| 6 | 最终 commit | 必做 |

**总时间估计：~2.75h**

---

### Task 1: 复制 BCI 简历 CSS 模板

**Files:**
- Copy from: `tracks/brain-computer-interface/notes/resume.css` (1KB)
- Copy to: `tracks/amd-rocm-python-backend/notes/resume.css`

- [ ] **Step 1: 验证源文件存在 + 目标目录存在**

Run:
```bash
ls -la /work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/notes/resume.css
ls -la /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/
```

Expected: 源文件存在（~1KB），目标目录存在且只有 `job-requirements.md`。

- [ ] **Step 2: 复制 CSS**

Run:
```bash
cp /work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/notes/resume.css \
   /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.css
```

- [ ] **Step 3: 验证复制成功**

Run:
```bash
diff /work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/notes/resume.css \
     /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.css
echo "exit: $?"
```

Expected: 无 diff 输出，exit code 0。

- [ ] **Step 4: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/learning-journey
git add tracks/amd-rocm-python-backend/notes/resume.css
git commit -m "chore(amd-resume): copy BCI resume.css as template"
```

Expected: 1 file changed, 53 insertions(+).

---

### Task 2: 修改通用 Resume.md（加求职意向 + 2 项目卡片 + 技能扩展）

**Files:**
- Modify: `notes/Resume.md` (59 行 → ~90 行)

- [ ] **Step 1: 读 BCI 简历作为风格参考（仅读，不修改）**

Run:
```bash
cat /work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/notes/resume.md
```

Expected: 显示 7.7KB 的 BCI 简历全文。注意其章节顺序 / 表格风格 / 粗体关键词用法。

- [ ] **Step 2: 备份原 Resume.md**

Run:
```bash
cp /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md \
   /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md.bak
```

- [ ] **Step 3: 写新 Resume.md（完整内容）**

Run (使用 Write 工具):
```bash
# 写入新内容到 /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md
```

完整内容：

```markdown
# 胡盛

- 电话：188-5665-3017
- 邮箱：hs3434@foxmail.com
- 个人网站：[hs3434.github.io](https://hs3434.github.io)
- **求职意向**：Python 后端 / K8s / 生信工程

---

## 教育背景

**西北农林科技大学** ｜ 植物科学与技术专业 ｜ 本科 ｜ 2018.09 - 2022.07 ｜ GPA：3.35

- 毕业论文：《基于逻辑斯蒂回归确定小麦倒伏相关性状及抗倒性状指标》
- 参与项目：《Rhizobium Inoculation Enhances the Resistance of Alfalfa and Microbial Characteristics in Copper-Contaminated Soil》（大学生科创项目，参与作者）
- 校园经历：学生会干部、班干、支教、家教老师等

## 工作经历

### 上海尤里卡信息科技有限公司 ｜ 生物信息工程师 ｜ 2025.04 - 至今

1. 将已有的医学转录组相关业务开发成自动化流程
2. 在服务器网络运维部署、代码开发、算法等方面为组内同事提供技术支持
3. **Docker 化 / Linux 服务端运维**：业务代码 Docker 化、systemd 服务管理、Nginx 反向代理

### 上海欧易生物医学科技有限公司 ｜ 生物信息研发工程师 ｜ 2022.08 - 2024.07

- **云平台生信工具开发**：R / Python / Linux / Docker / 云原生
- **业务自动化**：医学转录组业务流程自动化，模块化、可复用
- **平台地址**：[cloud.oebiotech.com](https://cloud.oebiotech.com/#/home)
- 主要技术：R、Python、Linux、Docker、云原生

### 上海欧易生物医学科技有限公司 ｜ 生物信息实习生 ｜ 2021.10 - 2022.01

- 单细胞转录组：质控、常规分析、售后、个性化分析
- 主要技术：单细胞转录组、R、Python、Linux

## 项目经验

### k8s-llm-runtime：OpenAI 兼容的 K8s vLLM 模型服务网关

- **背景**：vLLM 模型部署需 GPU + 容器 + 路由，团队多人共享时模型管理复杂
- **设计**：用 Helm chart + Python lib 抽象，让"加载/卸载模型"成为一行命令
- **实现**：双 chart（llm-inference + llm-router）+ lib 三层（K8sJobOperator / VLLMInferenceOperator / ModelOperator）
- **关键决策**：K8s Lease 分布式锁防 Router 多副本并发部署；ConfigMap 注入 aliases 避免镜像 rebuild
- **可观测性**：Prometheus 业务级 metrics（`chat_completions_duration_seconds` 等）+ structlog JSON 日志
- **质量**：31 commits / 90 tests pass / coverage 88% / ruff + mypy strict + helm-lint clean
- **仓库**：`work/run/projects/bio-24/my_projects/k8s-llm-runtime/`  ·  v0.1.0 tagged

### 脑机接口实时信号处理与解码软件

- 6 周学习路线产出：PyQt 实时 GUI + CNN 时空解码器（PyTorch，可选）
- 模块化信号处理 pipeline（滤波 / ICA / 时频），服务端 FastAPI 暴露
- 详见 `tracks/brain-computer-interface/notes/resume.md`

### 基于 Snakemake 的数据分析工作流框架

- **背景**：生物信息或数据分析的自动化流程通常使用 Snakemake 这类框架定义，但其上下游逻辑依赖静态的 rule 语法，无法实现模块的随意组合
- **新框架功能**：摈弃 Snakemake 原有的 rule 语法，直接调用内部接口，通过代码动态生成 rule 单元。只要规范输入输出类型，任意两个适配模块即可像积木一样拼接

### Linux 系统维护

- 出于兴趣长期租用 VPS 用于学习，维护 minio、nextcloud、mysql 等服务端应用
- 熟悉 Django 网络服务框架与 Nginx
- 自学网络技术，了解 IP/TCP 等网络协议体系，熟悉网络代理服务器搭建

### 机器学习与深度学习（PyTorch）

- 工作中常涉及数据分析，熟悉常见方法：统计检验、PCA、普氏分析等
- 自学深度学习，熟悉神经网络及 Transformer 架构

## 技能

- **编程**：C、C++、VB、R、Python（asyncio, type hints）、Matlab、SAS
- **平台/工具**：Linux、Docker、k8s、Helm、FastAPI、Pydantic、httpx、Prometheus、Grafana、PyTorch、Office
- **证书/语言**：C1 驾驶证、CET-4、普通话二级乙等

## 优势

具备较强的自主学习能力，特别是在数学和计算机方面，对计算机技术有很高的学习热情。
最近 6 周自学 K8s 后端栈，独立完成 v0.1.0 tagged 的完整项目。
```

- [ ] **Step 4: 行数 + 关键词自检**

Run:
```bash
wc -l /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md
grep -c "k8s-llm-runtime" /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md
grep -c "Docker" /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md
grep -c "k8s" /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md
grep -c "Helm" /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md
grep -c "Prometheus" /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md
```

Expected:
- 行数：~90 行（不严格）
- k8s-llm-runtime: ≥ 1
- Docker: ≥ 1
- k8s: ≥ 1
- Helm: ≥ 1
- Prometheus: ≥ 1

- [ ] **Step 5: 求职意向首屏可见性检查**

Run:
```bash
head -10 /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md | grep "求职意向"
```

Expected: 输出包含 "求职意向"。

- [ ] **Step 6: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/learning-journey
git add notes/Resume.md
git commit -m "docs(resume): add k8s-llm-runtime + BCI project cards, extend skills to K8s stack"
```

Expected: 1 file changed, ~30 insertions(+), ~5 deletions(-).

---

### Task 3: 创建 amd-rocm 专用 resume.md（按 JD 定制）

**Files:**
- Create: `tracks/amd-rocm-python-backend/notes/resume.md` (~180 行)

**对照 JD 项**（来自 `notes/job-requirements.md`）：
- 🔴 硬性：Python 后端 2 年+ → 工作经历 + 4 层技能栏
- 🔴 硬性：Docker/k8s → 技能栏 + k8s-llm-runtime 深度
- 🔴 加分：AI/GPU → k8s-llm-runtime 强调 vLLM
- 🔴 加分：ML 平台 → Snakemake 强化"类 Argo Workflows"
- 🟡 加分：GPU 集群 → k8s-llm-runtime 强调 GPU vendor 切换
- 🟡 加分：Python 后端强化 → FastAPI / async / Pydantic
- 现场 demo → 个人优势显式

- [ ] **Step 1: 重读 JD + BCI 简历模板**

Run:
```bash
cat /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/job-requirements.md
echo "==="
cat /work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/notes/resume.md
```

Expected: 看到 JD 56 行 + BCI 简历 7.7KB 全文。

- [ ] **Step 2: 写 amd-rocm 专用 resume.md（完整内容）**

Run (使用 Write 工具): 写入 `/work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.md`

完整内容：

```markdown
# 胡盛

- 电话：188-5665-3017
- 邮箱：hs3434@foxmail.com
- 个人网站：[hs3434.github.io](https://hs3434.github.io)
- **求职意向**：AMD ROCm Python 后端开发工程师（ROCm Radeon Cloud 方向）

---

## 个人简介

3 年生物信息工程化经验，自学转型 K8s 后端栈。
专注**容器化部署、资源调度、任务编排、GPU 推理服务**。
最近 6 周自学 ROCm / K8s / Helm / FastAPI / Prometheus，独立完成 **k8s-llm-runtime**（K8s 上的 vLLM 模型服务网关），**v0.1.0 tagged，可现场跑 demo**。
熟悉 Snakemake 类 Argo Workflows 的 ML 平台抽象。

---

## 求职技能（按岗位匹配排序，4 层）

### 后端核心

- Python 3.11+（asyncio, type hints, Pydantic, httpx async）
- FastAPI（OpenAPI / dependency injection / lifespan）
- 测试：pytest, pytest-asyncio, 88% coverage

### 容器与编排

- Docker（multi-stage 构建，Alpine 镜像优化）
- Kubernetes（Pod / Service / Deployment / StatefulSet / ConfigMap / RBAC）
- Helm chart（values 模板化，helm install/upgrade/uninstall，CI lint clean）
- 镜像仓库：registry.k8s.io / docker.io / ghcr.io / nvcr.io（国内 DaoCloud 镜像加速）

### GPU / LLM 生态

- vLLM（OpenAI 兼容 API，推理服务）
- AMD ROCm 基础（HSA / HIP 概念，amd.com/gpu 资源调度）
- PyTorch（CNN 时空解码器 / Transformer）
- Hugging Face（transformers 库，tokenizer）

### 可观测性与工具链

- Prometheus（prometheus_client，histogram / counter / gauge）
- structlog（JSON structured logging）
- uv / ruff / mypy strict / GitHub Actions
- Linux 服务端运维（systemd, Nginx, 端口/进程管理）

---

## 项目经验

### k8s-llm-runtime：K8s 上的 vLLM 模型服务网关（v0.1.0 tagged）

**问题**（对应 JD 职责 1 + 3）：vLLM 模型部署需 GPU + 容器 + 路由，团队多人共享时模型管理复杂；研究/小团队想用 OpenAI 兼容 API 时门槛高。
（直接对应 JD："大模型训练/推理 Workshop、教程、功能演示"）

**架构**（双 chart + 三层 lib + 镜像优化）：
- `charts/llm-inference/`：vLLM 负载 chart，**GPU vendor 切换仅靠 `values.yaml`**
  （amd.com/gpu / nvidia.com/gpu / none 三态，values 显式选择）
- `charts/llm-router/`：FastAPI 网关 chart
  - ConfigMap 注入 initContainer 加载兄弟 chart
  - RBAC 最小权限（Pod/Service/ConfigMap read+write + Lease）
  - ServiceMonitor 可选启用（Service 0.0.0.0:9090/metrics）
- `src/k8s_llm_runtime/`：3 层 lib 抽象
  - `K8sJobOperator`（低层，通用 Job 调度）
  - `VLLMInferenceOperator`（中层，helm CLI subprocess + GPU vendor）
  - `ModelOperator`（高层，OpenAI 兼容 + 自动部署）

**4 大技术亮点**：
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
   - ServiceMonitor 可选进 Grafana

**GPU vendor 切换 demo**（对应 JD 加分 GPU 集群）：
- values.yaml `gpu.vendor=amd|nvidia|none`
- AMD：amd.com/gpu 资源调度，ROCm vLLM 镜像
- NVIDIA：nvidia.com/gpu 资源调度，CUDA vLLM 镜像
- none：CPU only 模式（kind cluster 默认，本地开发用）

**质量保证**：
- 31 commits / 90 tests pass / coverage 88%
- ruff + mypy strict + helm-lint 全 clean
- 2 Helm charts（llm-inference + llm-router）

**踩坑与修复**：
- Service DNS 不匹配 bug：`--set fullnameOverride={release_name}` 修复
- kind 节点国内镜像加速：containerdConfigPatches + DaoCloud mirror
- 这些都写入 `docs/amd-interview-demo.md` 供现场参考

**未来**（v1.1）：SSE 流式推理 / RBAC 收紧只读 / 真实 GPU 集群 e2e

### 基于 Snakemake 的 ML 平台工作流框架（生信背景，类 Argo Workflows）

- 背景：Snakemake rule 语法无法实现模块随意组合
- 设计：摈弃 rule 语法，直接调内部接口动态生成 rule，规范输入输出类型即可积木式拼接
- 关联：JD 加分项"机器学习平台研发经验"——本项目是 ML 平台抽象的工程实践

### 脑机接口 CNN 解码器（PyTorch）—— 6 周学习路线产出

- 端到端时空卷积解码 EEG 信号
- PyQt 实时 GUI + FastAPI 暴露
- 详见 BCI 专用简历 `tracks/brain-computer-interface/notes/resume.md`

---

## 工作经历

### 上海尤里卡信息科技有限公司 ｜ 生物信息工程师 ｜ 2025.04 - 至今

- **Docker 部署**：业务代码 Docker 化（基于 snakemake + 自研框架）
- **服务端运维**：Linux 服务器日常维护，Nginx 反向代理，systemd 服务管理
- **云平台工具开发**：业务自动化流程 + 算法工具

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

- **6 周自学 K8s 后端栈**：从零到 v0.1.0 tagged 项目，独立完成双 Helm chart + Python lib
- **现场 demo 能力**：可自带电脑在 kind cluster 上跑通完整 LLM 推理流程（部署 → 路由 → chat completions → metrics）
- **学习能力强**：3 年内从生物信息跨界到 K8s 后端，技术热情高
- **3 年 Python 工程化经验**：从科研脚本到云平台工具的完整路径
```

- [ ] **Step 3: 关键词自检（JD 关键词命中）**

Run:
```bash
F=/work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.md
echo "JD 关键词命中检查："
for kw in "AMD ROCm" "vLLM" "Helm" "k8s" "Prometheus" "容器化" "资源调度" "Snakemake" "Argo Workflows" "现场 demo" "FastAPI" "ConfigMap" "Lease" "RBAC"; do
  n=$(grep -c "$kw" $F)
  printf "  %-20s : %d\n" "$kw" "$n"
done
```

Expected: 每个关键词至少出现 1 次。`AMD ROCm` / `vLLM` / `Helm` / `k8s` / `Prometheus` / `容器化` 应各 ≥ 2。

- [ ] **Step 4: 行数检查**

Run:
```bash
wc -l /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.md
```

Expected: 100-200 行。

- [ ] **Step 5: 求职意向首屏检查**

Run:
```bash
head -10 /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.md | grep "AMD ROCm"
```

Expected: 输出包含 "AMD ROCm"。

- [ ] **Step 6: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/learning-journey
git add tracks/amd-rocm-python-backend/notes/resume.md
git commit -m "docs(amd-resume): JD-tailored resume with 4-layer skills + k8s-llm-runtime deep dive"
```

Expected: 1 file changed, ~180 insertions(+).

---

### Task 4: weasyprint 导出 amd-rocm 专用 resume.pdf

**Files:**
- Create: `tracks/amd-rocm-python-backend/notes/resume.pdf` (weasyprint 导出)

- [ ] **Step 1: 检查 weasyprint / wkhtmltopdf 可用性**

Run:
```bash
which weasyprint wkhtmltopdf pandoc 2>&1
python3 -c "import weasyprint; print(weasyprint.__version__)" 2>&1
```

Expected: 至少 weasyprint 可用（BCI 路线已用）。如 weasyprint 不可用但 wkhtmltopdf 可用，回退用 wkhtmltopdf。

- [ ] **Step 2: 切换到目标目录导出 PDF**

Run:
```bash
cd /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/
weasyprint resume.md resume.pdf --stylesheet resume.css 2>&1
ls -la resume.pdf
```

Expected:
- weasyprint 命令无 error 退出
- resume.pdf 文件存在（~50-200KB）

- [ ] **Step 3: 验证 PDF 页数**

Run:
```bash
pdfinfo resume.pdf 2>&1 | grep -E "Pages|Page size"
```

Expected: Pages: 2-3（amd-rocm 简历比通用简历长 1-2 页，因为 k8s-llm-runtime 展开 12-16 行）。

如果 weasyprint 不可用，回退：
```bash
pandoc resume.md -o resume.pdf --pdf-engine=wkhtmltopdf --css resume.css
```

- [ ] **Step 4: PDF 渲染快速抽检**

Run:
```bash
pdftotext resume.pdf - | head -30
```

Expected: 输出包含 "AMD ROCm" / "k8s-llm-runtime" / "FastAPI" 等关键词。

- [ ] **Step 5: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/learning-journey
git add tracks/amd-rocm-python-backend/notes/resume.pdf
git commit -m "docs(amd-resume): export PDF via weasyprint"
```

Expected: 1 file changed, ~130KB inserted (PDF binary).

---

### Task 5: 整体验证（DoD 自检）

- [ ] **Step 1: 通用 Resume.md 验证**

Run:
```bash
F=/work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md
echo "=== 通用 Resume.md 验证 ==="
echo "1. 行数: $(wc -l < $F)"
echo "2. 求职意向首屏: $(head -10 $F | grep -c '求职意向')"
echo "3. 项目数（含 ### ）: $(grep -c '^### ' $F)"
echo "4. k8s-llm-runtime 卡片: $(grep -c 'k8s-llm-runtime' $F)"
echo "5. BCI 卡片: $(grep -c '脑机接口' $F)"
echo "6. K8s 关键词: $(grep -cE 'k8s|Docker|Helm|Prometheus' $F)"
```

Expected:
1. 行数 ≤ 100
2. 求职意向 ≥ 1
3. 项目数 = 5
4. k8s-llm-runtime ≥ 1
5. 脑机接口 ≥ 1
6. K8s 关键词 ≥ 5

- [ ] **Step 2: amd-rocm 专用简历验证**

Run:
```bash
F=/work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.md
echo "=== amd-rocm 简历验证 ==="
echo "1. 行数: $(wc -l < $F)"
echo "2. 求职意向 AMD ROCm: $(head -10 $F | grep -c 'AMD ROCm')"
echo "3. 4 层技能栏: $(grep -c '^### ' $F)"  # 期望 6 (后端核心 / 容器与编排 / GPU / 可观测性 / 项目1-2 / 工作3段 / 教育 / 优势)
echo "4. k8s-llm-runtime 出现次数: $(grep -c 'k8s-llm-runtime' $F)"
echo "5. Snakemake 类比: $(grep -c 'Argo Workflows' $F)"
echo "6. 现场 demo: $(grep -c '现场 demo' $F)"
```

Expected:
1. 行数 100-200
2. AMD ROCm ≥ 1
3. 4 层技能栏 + 多个 ### 标题（≥ 8）
4. k8s-llm-runtime ≥ 3（项目标题 + 4 大亮点中多次）
5. Argo Workflows = 1
6. 现场 demo = 1

- [ ] **Step 3: 简历 PDF 验证**

Run:
```bash
F=/work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.pdf
echo "=== resume.pdf 验证 ==="
echo "1. 文件大小: $(ls -la $F | awk '{print $5}') bytes"
echo "2. PDF magic: $(file $F | grep -c 'PDF document')"
echo "3. 页数: $(pdfinfo $F 2>/dev/null | grep '^Pages' | awk '{print $2}')"
```

Expected:
1. 文件大小 50KB-300KB
2. PDF magic = 1
3. 页数 2-3

- [ ] **Step 4: css 复用验证**

Run:
```bash
diff /work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/notes/resume.css \
     /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/resume.css
echo "diff exit: $?"
```

Expected: 无 diff 输出，exit 0（css 完全复用）。

- [ ] **Step 5: 整体 git status 检查**

Run:
```bash
cd /work/run/projects/bio-24/my_projects/learning-journey
git status
git log --oneline -5
```

Expected:
- `git status` 输出 clean（无未提交）
- 最近 5 个 commit 包含 4 个新 commit（css + Resume.md + resume.md + resume.pdf）

---

### Task 6: 最终 commit 收尾（如有遗漏）

- [ ] **Step 1: 检查未提交残留**

Run:
```bash
cd /work/run/projects/bio-24/my_projects/learning-journey
git status -s
```

Expected: 无输出（clean）。

如有未提交残留（例如 .bak 文件），运行：
```bash
rm -f /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md.bak
git status -s
```

- [ ] **Step 2: 删除备份文件**

Run:
```bash
ls /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md.bak 2>/dev/null && \
  rm /work/run/projects/bio-24/my_projects/learning-journey/notes/Resume.md.bak
ls /work/run/projects/bio-24/my_projects/learning-journey/notes/
```

Expected: 无 .bak 文件。

- [ ] **Step 3: 最终 git log 摘要**

Run:
```bash
cd /work/run/projects/bio-24/my_projects/learning-journey
git log --oneline -7
git log --stat -1
```

Expected: 显示简历相关的 4 个 commit，每个 commit 信息清晰。

---

## Definition of Done（阶段 1 完成标准）

- [ ] `tracks/amd-rocm-python-backend/notes/resume.css` 存在（与 BCI 完全相同）
- [ ] `notes/Resume.md` 含求职意向 + 5 项目（含 k8s-llm-runtime + BCI 轻提）
- [ ] `tracks/amd-rocm-python-backend/notes/resume.md` 按 JD 定制，4 层技能栏，关键词命中
- [ ] `tracks/amd-rocm-python-backend/notes/resume.pdf` weasyprint 导出 2-3 页
- [ ] 4 个 git commit 提交到 main 分支
- [ ] 无 .bak 残留文件
- [ ] 无 "TBD / TODO / 略 / 待补充" 标记

## 阶段 2 推迟说明

本 plan 仅覆盖 spec 阶段 1（4 文件，~2.75h）。spec 阶段 2（1-pager / 5min-pitch / whiteboard-qa / architecture.mmd，共 4 文件 ~3.5h）按用户指示"先弄好简历其他的再说"推迟。阶段 1 完成后，按需重新走 brainstorm → write plan 流程。

## 参考资源

- **Spec**：`docs/superpowers/specs/2026-06-24-amd-interview-prep-design.md`（commit `6bbd213`）
- **JD 对照**：`tracks/amd-rocm-python-backend/notes/job-requirements.md`（56 行）
- **BCI 简历模板**：`tracks/brain-computer-interface/notes/resume.md`（7.7KB）+ `resume.css`（1KB）
- **k8s-llm-runtime**：`/work/run/projects/bio-24/my_projects/k8s-llm-runtime/`（v0.1.0 tagged, commit `0bf3a3a`）
