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
- **仓库**：[github.com/hs3434/k8s-llm-runtime](https://github.com/hs3434/k8s-llm-runtime)  ·  v0.1.0 tagged

### 脑机接口实时信号处理与解码软件

- 6 周学习路线产出：PyQt 实时 GUI + CNN 时空解码器（PyTorch，可选）
- 模块化信号处理 pipeline（滤波 / ICA / 时频），服务端 FastAPI 暴露
- 详见 BCI 路线简历 [github.com/hs3434/bci-pipeline-demo](https://github.com/hs3434/bci-pipeline-demo)

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
