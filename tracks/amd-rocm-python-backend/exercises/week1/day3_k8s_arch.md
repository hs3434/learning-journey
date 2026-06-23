# Day 3: Kubernetes 架构 + kubectl 基础

## 1. K8s 是什么？

Kubernetes（K8s）是**容器编排平台**，由 Google 开源。核心能力：
- 自动化部署、扩缩容
- 服务发现与负载均衡
- 自愈（容器崩溃自动重启、节点故障自动迁移）
- 滚动更新与回滚
- 配置与密钥管理
- 存储编排
- 批处理

> **Docker Compose** vs **K8s**：Compose 是单机编排；K8s 是**集群**编排，支持跨主机调度、自愈、声明式 API。

## 2. K8s 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    Control Plane                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  API     │  │  etcd    │  │Scheduler │  │Controller│ │
│  │  Server  │  │  (存储)  │  │(调度)    │  │ Manager  │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ (kubectl 提交 YAML → API Server)
┌────────────────────────▼────────────────────────────────┐
│                    Worker Nodes                          │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ kubelet  kube-proxy│  │ kubelet  kube-proxy│            │
│  │ ┌──────┐ ┌──────┐ │  │ ┌──────┐ ┌──────┐ │             │
│  │ │ Pod  │ │ Pod  │ │  │ │ Pod  │ │ Pod  │ │             │
│  │ └──────┘ └──────┘ │  │ └──────┘ └──────┘ │             │
│  └──────────────────┘  └──────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 角色 |
|------|------|
| **API Server** | K8s 前端，接收所有请求（kubectl/Helm/UI）|
| **etcd** | 分布式 KV 存储，K8s 集群唯一状态源 |
| **Scheduler** | 决定 Pod 跑在哪个 Node |
| **Controller Manager** | 维护集群状态（如 Deployment 副本数）|
| **kubelet** | Node 上的 agent，管理 Pod 生命周期 |
| **kube-proxy** | Node 上的网络代理，维护 Service 规则 |
| **Pod** | K8s 最小调度单位（可含 1+ 容器）|

## 3. 核心对象模型（Workload API）

```
Deployment  (无状态应用)    ←── 最常用
  └── ReplicaSet            ←── 副本集（由 Deployment 管理）
        └── Pod             ←── 实际跑容器
              └── Container

StatefulSet    (有状态应用，如数据库)
DaemonSet      (节点级守护进程，如日志收集)
Job / CronJob  (批处理 / 定时任务)
```

## 4. 部署一个 Pod 的流程

```bash
# 写一个 yaml → kubectl apply → API Server 接收
# → Scheduler 选 Node → kubelet 启动容器 → etcd 记录状态
# → kubectl get pod 看到 Running
```

## 5. kubectl 必备命令

### 集群信息

```bash
kubectl version                                    # 版本
kubectl cluster-info                               # 集群信息
kubectl get nodes                                  # 节点列表
kubectl get nodes -o wide                          # 详细信息
```

### 查看资源

```bash
kubectl get pods                                   # 当前 namespace 的 pod
kubectl get pods -A                                # 所有 namespace
kubectl get pods -n kube-system                    # 指定 namespace
kubectl get pods -o wide                           # 多列信息（IP、Node）
kubectl get pods -o yaml                           # 完整 yaml
kubectl get pods --show-labels                     # 显示标签

kubectl get all                                    # 所有常用资源
kubectl get deploy,svc,ing                         # 多种资源
```

### 描述资源（调试必备）

```bash
kubectl describe pod <pod-name>                    # 详细信息 + 事件
kubectl describe node <node-name>                  # 节点详情
kubectl describe svc <svc-name>
```

### 创建 / 更新 / 删除

```bash
kubectl apply -f app.yaml                          # 声明式（推荐）
kubectl apply -f dir/                              # 应用目录下所有 yaml
kubectl apply -f https://...                       # 直接用 URL

kubectl delete -f app.yaml                         # 按文件删
kubectl delete pod <pod-name>                      # 按名称删
kubectl delete pod --all -n dev                    # 全删
```

### 调试

```bash
kubectl logs <pod-name>                            # 容器日志
kubectl logs <pod-name> -c <container>             # 多容器 Pod 指定容器
kubectl logs <pod-name> -f                         # 跟踪日志
kubectl logs <pod-name> --previous                 # 上一次启动的日志（崩溃后）

kubectl exec -it <pod-name> -- bash                # 进入容器
kubectl exec -it <pod-name> -- sh                  # alpine 镜像用 sh

kubectl port-forward <pod-name> 8080:80            # 端口转发（本地调试）

kubectl cp <pod-name>:/path/in/pod /local/path    # 文件拷贝
```

### 扩缩容

```bash
kubectl scale deploy/<name> --replicas=5
kubectl autoscale deploy/<name> --min=2 --max=10 --cpu-percent=80   # HPA
```

## 6. 第一个 Pod 实战

见同目录 `day3_pod.yaml`：

```bash
# 启动 minikube
minikube start --driver=docker

# 应用
kubectl apply -f day3_pod.yaml

# 查看
kubectl get pod my-pod
kubectl describe pod my-pod
kubectl logs my-pod

# 进入
kubectl exec -it my-pod -- bash
# 容器内：
#   ls /
#   env | grep MY_VAR
#   exit

# 删除
kubectl delete -f day3_pod.yaml
```

## 7. 命名空间（Namespace）

K8s 用 Namespace 做资源隔离（多租户、环境隔离）。

```bash
kubectl get ns
kubectl create namespace dev
kubectl config set-context --current --namespace=dev
```

## 8. 上下文与配置

```bash
kubectl config get-contexts                        # 当前所有 context
kubectl config current-context                     # 当前 context
kubectl config use-context minikube                # 切换
```

`~/.kube/config` 文件管理多个集群的连接信息。

## 9. 实战任务

按 `day3_kubectl_cheatsheet.sh` 中的命令顺序执行，把每个命令的输出记录到 `day3_output.log`。

## 10. 重要概念区分

| 概念 | 说明 |
|------|------|
| **Pod** | 调度的最小单位（可含多容器，通常 1 个）|
| **Deployment** | 声明"我要 N 个 Pod"，由它创建 ReplicaSet |
| **Service** | 给一组 Pod 提供稳定 IP + 负载均衡 |
| **Namespace** | 资源隔离单位 |
| **Label** | 键值对，K8s 通过 label selector 关联资源 |
| **Annotation** | 非标识性元数据（工具/客户端用）|

## 参考资料

- [Kubernetes 官方文档（中文）](https://kubernetes.io/zh-cn/docs/home/)
- [kubectl 命令参考](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
- [K8s 中文实战（阳明）](https://www.yuque.com/xiangguo/it3aew/)