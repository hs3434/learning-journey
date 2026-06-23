# Day 4: Pod 生命周期 + Deployment + ReplicaSet

## 1. 为什么需要 Deployment？

直接创建 Pod 有问题：
- Pod 挂了不会自动重建
- 多副本需要手动管理
- 滚动更新/回滚困难

**Deployment** = "我想要 N 个相同的 Pod" 的**声明**，K8s 控制器会持续**对齐**实际状态与期望状态。

## 2. 三层关系

```
Deployment  (期望状态: 3 个 Pod, image=v2)
   │
   ├── manages ──> ReplicaSet (自动创建)
   │                  │
   │                  └── creates ──> Pod × 3
   │                                       │
   │                                       └── Container (FastAPI)
   │
   └── 滚动更新：创建新 RS (v2) → 旧 RS (v1) 副本数递减 → 替换
```

关键点：**Deployment 不直接管 Pod**，而是通过 ReplicaSet 管。这让**版本切换**和**回滚**成为可能。

## 3. Pod 生命周期

```
Pending ──> Running ──> Succeeded / Failed
                    │
                    └──> Unknown（节点失联）

# 容器状态：
Waiting → Running → Terminated
```

### 常见 Pending 原因

- 镜像拉取失败（imagePullBackOff）
- 资源不足（CPU/内存）
- 节点选择器不匹配
- PVC 未绑定

### 常见 CrashLoopBackOff

容器启动后立即退出，K8s 重启，循环崩溃。调试：

```bash
kubectl logs <pod> --previous      # 看上次启动日志
kubectl describe pod <pod>         # 看 Events
```

## 4. Deployment YAML 关键字段

```yaml
apiVersion: apps/v1                # 注意：Deployment 用 apps/v1
kind: Deployment
metadata:
  name: app-deploy
  labels:
    app: fastapi
spec:
  replicas: 3                      # 副本数
  selector:                        # 必须匹配 template.labels
    matchLabels:
      app: fastapi
  strategy:                        # 更新策略
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1                  # 最多超出 replicas 几个
      maxUnavailable: 0            # 最多不可用几个（0 = 不停服）
  template:                        # Pod 模板
    metadata:
      labels:                      # ⚠️ 必须与 selector.matchLabels 一致
        app: fastapi
    spec:
      containers:
      - name: app
        image: fastapi-app:v1
        ports:
        - containerPort: 8000
        resources:
          requests:                # 调度依据
            memory: "128Mi"
            cpu: "250m"
          limits:                  # 硬上限
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:             # 存活探针（失败则重启容器）
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 15
        readinessProbe:            # 就绪探针（失败则从 Service 摘除）
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 3
          periodSeconds: 5
```

## 5. 健康探针详解

| 探针 | 作用 | 失败后果 |
|------|------|----------|
| `livenessProbe` | 容器是否还活着 | 重启容器 |
| `readinessProbe` | 容器是否可接流量 | 从 Service Endpoints 摘除 |
| `startupProbe` | 慢启动应用是否完成启动 | 抑制 liveness 检查 |

支持的检测方式：
- `httpGet`：HTTP GET，2xx/3xx 算成功
- `tcpSocket`：TCP 端口能否连上
- `exec`：在容器内执行命令，exit 0 算成功
- `grpc`：gRPC 健康检查（K8s 1.24+）

## 6. 资源 requests vs limits

- **requests**：调度器决定 Pod 跑哪个 Node 的依据
- **limits**：容器运行时硬限制（超出则 OOM Kill 或 CPU throttling）

⚠️ **CPU 是可压缩资源**（超限 throttle），**内存是不可压缩资源**（超限 OOM Kill）。

## 7. 实战：部署 FastAPI Deployment

完整 manifest 见 `day4_deployment.yaml`。

```bash
# 1. 构建镜像（用 Day 1 的多阶段 Dockerfile）
cd /work/learning-journey/tracks/amd-rocm-python-backend/exercises/week1
docker build -t fastapi-app:v1 -f k8s-local-stack/Dockerfile k8s-local-stack/

# 2. 加载到 minikube（minikube 用独立 Docker daemon）
minikube image load fastapi-app:v1
# 或者直接用 minikube 的 docker env：
# eval $(minikube docker-env)  # 后续 docker build 会进 minikube daemon
# docker build -t fastapi-app:v1 ...

# 3. 部署
kubectl apply -f day4_deployment.yaml

# 4. 查看
kubectl get deploy
kubectl get rs
kubectl get pods -o wide
kubectl get pods -l app=fastapi    # 用 label 选择器

# 5. 模拟容器崩溃，验证自愈
POD_NAME=$(kubectl get pod -l app=fastapi -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD_NAME -- kill 1
# 观察：kubectl get pods 中该 Pod 会先 Terminating，再被 Deployment 拉起新 Pod

# 6. 扩容到 5 个
kubectl scale deploy/fastapi-deploy --replicas=5
kubectl get pods -l app=fastapi

# 7. 缩容到 2 个
kubectl scale deploy/fastapi-deploy --replicas=2

# 8. 滚动更新到 v2
docker build -t fastapi-app:v2 -f k8s-local-stack/Dockerfile k8s-local-stack/
minikube image load fastapi-app:v2
kubectl set image deploy/fastapi-deploy app=fastapi-app:v2
# 实时观察
kubectl rollout status deploy/fastapi-deploy
kubectl get rs    # 看到两个 RS（v1, v2）

# 9. 回滚到 v1
kubectl rollout undo deploy/fastapi-deploy
kubectl rollout history deploy/fastapi-deploy

# 10. 清理
kubectl delete -f day4_deployment.yaml
```

## 8. 滚动更新策略

| 策略 | 行为 | 适用 |
|------|------|------|
| `RollingUpdate`（默认）| 逐步替换旧 Pod | Web 服务 |
| `Recreate` | 先全删旧的再起新的 | 有状态、不支持多版本并存 |

`maxSurge` + `maxUnavailable` 控制更新速度：
- `maxSurge=1, maxUnavailable=0`：永远保证 N 个可用，最多临时 N+1 个
- `maxSurge=0, maxUnavailable=1`：更新期间可能只有 N-1 个可用

## 9. 实战任务清单

1. ✅ 部署 3 副本 FastAPI
2. ✅ 触发 CrashLoopBackOff，观察 K8s 重启
3. ✅ 扩容/缩容
4. ✅ 滚动更新到 v2
5. ✅ 回滚到 v1
6. ✅ 修改资源 limits，故意超出看 OOM 行为
7. ✅ 修改 readinessProbe 路径为 `/nonexistent`，看 Pod 状态变 NotReady

## 参考资料

- [Deployment 官方文档](https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/deployment/)
- [Pod 生命周期](https://kubernetes.io/zh-cn/docs/concepts/workloads/pods/pod-lifecycle/)
- [健康探针配置](https://kubernetes.io/zh-cn/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)