# AMD ROCm Python 后端开发工程师 — 短板补齐分析

> 完整 JD 见 `notes/require.md`，本文档聚焦"必备 vs 加分"项，便于对照学习计划。

## 背景

3 年 Python（生信 + BCI），熟悉 Docker/云原生/PyTorch/Transformer，缺 K8s 实战与大模型项目经验。目标岗位：**AMD ROCm Python 后端开发工程师**（ROCm Radeon Cloud 生态）。

## 岗位职责

1. 开发 AMD ROCm Radeon Cloud 的各种模块功能（大模型训练/推理 Workshop、教程、功能演示）
2. 负责公司平台型软件的后端研发、设计和实现
3. 基于容器化部署、资源调度、任务编排、集群运维、数据集管理等角度解决技术问题

## 核心技能要求（硬性）

| 类别 | 要求 | 现状 | 匹配度 |
|------|------|------|--------|
| 学历 | 统招本科（计算机/软件工程相关专业优先）| 西农本科（植物科学与技术）| ✅ 满足最低学历 |
| Python 后端 | 2 年以上 Python 后端开发经验 | 3 年 Python（Django 经验）| ⚠️ 时长够，需转向后端定位 |
| 容器技术 | 熟悉 Docker/k8s，具备使用部署经验 | Docker 基础有，K8s 零基础 | ❌ **第一大缺口** |
| 英语 | 基础读写，无需海外沟通 | CET-4，能读技术文档 | ✅ 满足 |

## 加分项

| 类别 | 要求 | 现状 | 匹配度 |
|------|------|------|--------|
| 前端开发 | 掌握前端开发技术 | 无 | ❌ 优先级最低 |
| AI / GPU 项目 | 大模型训练/推理经验 | PyTorch + Transformer（EEG 领域）| ⚠️ **第二大缺口**——方向对、领域错 |
| ML 平台 | 机器学习平台研发经验 | Snakemake 自研框架（类 Argo Workflows）| ⚠️ 可类比 |
| GPU 集群 | 熟悉 GPU 集群架构 | 仅单机 CPU | ❌ 需补 ROCm/HIP 基础 |
| PostgreSQL | 数据库 | 有 MySQL | ⚠️ 需补 PG |
| Redis | 缓存 | 无 | ❌ Week 3 补 |
| Kafka | 消息队列 | 无 | ❌ Week 3 补 |
| 对象存储 | MinIO/Ceph/S3 | 有 MinIO 经验 | ✅ 直接复用 |
| 高速存储 | NVMe/Ceph/Weka | 无 | 🟢 优先级低 |

## 关键缺口优先级

1. 🔴 **Kubernetes**：硬性一票否决，必须 4 周内达到"独立部署 Python Web 到 K8s"水平
2. 🔴 **大模型项目经验**：加分但权重高，需补充 LLM 推理/Hugging Face 实战
3. 🟡 **ROCm / GPU 生态**：理解 ROCm 与 CUDA 差异，能跑通 ROCm 容器 demo
4. 🟡 **Python 后端强化**：从 Django 迁移到 FastAPI + 异步
5. 🟢 **前端基础**：React 入门级，AMD Workshop 可能需要简单页面
6. 🟢 **数据库/中间件**：PG/Redis/Kafka 在 Week 3 顺带补

## 面试信息

- **流程**：1 轮技术面（代码测试 + 工作经验）
- **形式**：prefer 现场 F2F，需**自带电脑**
- **汇报线**：Vincent Fang（ROCm 软件解决方案架构师）
- **建议**：现场跑 K8s 部署 + LLM 推理 demo

## 备注

完整岗位 JD 保留在 `notes/require.md`，本文档为对照学习计划使用的精简版。详细学习路径见 `plans/learning-plan-amd-rocm.md`。