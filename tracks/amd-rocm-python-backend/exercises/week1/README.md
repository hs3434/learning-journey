# Week 1 — Docker 深入 + K8s 核心

**主线**：从"会用 Docker"到"能在 K8s 上部署 Python Web 应用"。

**对应岗位要求**：
- 🔴 Docker（生产化实践）
- 🔴 Kubernetes（核心概念 + 部署能力）— **第一大缺口**

**周产出**：`k8s-local-stack` 项目（FastAPI + minikube 本地部署）

---

## 每日节奏（3-4h）

| Day | 主题 | 产出 |
|-----|------|------|
| 1 | Docker 多阶段构建、Dockerfile 优化、layer 缓存 | 对比镜像尺寸 |
| 2 | Docker Compose 多容器编排 | 跑通 FastAPI + Redis + PG |
| 3 | K8s 架构、kubectl 基础 | minikube 启动 + 基本命令 |
| 4 | Pod 生命周期、Deployment、ReplicaSet、滚动更新 | 部署 FastAPI Deployment |
| 5 | Service 三种类型（ClusterIP/NodePort/LoadBalancer）| NodePort 暴露 FastAPI |
| 6 | ConfigMap + Secret + Volume 挂载 | 带配置的 FastAPI |
| 7 | 复盘 + 整合项目 | k8s-local-stack |

---

## 前置环境

```bash
# Docker
docker --version
docker run hello-world

# minikube（K8s 本地）
minikube start --driver=docker

# kubectl
kubectl version --client
kubectl get nodes

# Python 3.11+
python3 --version
```

## 学习路径

```
Day1 (Dockerfile) ─┐
Day2 (Compose)    ─┼─→ Day3 (K8s 入门) → Day4-6 (核心资源) → Day7 (整合)
                  │
```

从 Day 1-2 巩固容器化基础（你已有 Docker 经验，重点是**多阶段构建**和生产化实践），Day 3 起进入 K8s 主线。每天的代码文件都可以独立运行/部署。

## 与岗位 JD 的对应

| 任务 | 对应要求 |
|------|----------|
| 多阶段 Dockerfile | 容器技术、Docker 实践 |
| docker-compose | 本地多服务开发（与 AMD 平台型软件一致）|
| K8s 部署 FastAPI | Kubernetes 使用部署经验（**硬性**）|
| ConfigMap/Secret | 任务编排、数据集管理（岗位职责）|
| Resource limits | 资源调度、集群运维（岗位职责）|