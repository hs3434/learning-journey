# k8s-local-stack

基于 Kubernetes 的 Python Web 应用完整部署示例，对应 AMD ROCm Python 后端岗位要求。

## 功能

- FastAPI 后端，3 副本 Deployment
- 多阶段 Dockerfile 优化镜像体积
- ConfigMap 注入配置 + Volume 挂载
- Secret 注入敏感信息
- 完整健康探针（liveness / readiness / startup）
- 资源 requests / limits
- 滚动更新 + 自愈演示
- 三种 Service 模式（ClusterIP / NodePort / Headless）

## 项目结构

```
k8s-local-stack/
├── README.md
├── pyproject.toml
├── Dockerfile
├── .dockerignore
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── api/
│       ├── __init__.py
│       └── routes.py
└── k8s/
    ├── 00-namespace.yaml
    ├── 10-configmap.yaml
    ├── 20-secret.yaml
    ├── 30-deployment.yaml
    └── 40-service.yaml
```

## 快速开始

```bash
# 启动 minikube
minikube start --driver=docker

# 构建并加载镜像
docker build -t k8s-local-stack:v1 .
minikube image load k8s-local-stack:v1

# 部署
kubectl apply -f k8s/

# 等待就绪
kubectl -n k8s-demo wait --for=condition=Ready pod -l app=k8s-local-stack --timeout=60s

# 端口转发
kubectl -n k8s-demo port-forward svc/k8s-local-stack-svc 8000:80

# 测试
curl http://localhost:8000/
curl http://localhost:8000/config
curl http://localhost:8000/health
```

## 演示场景

### 1. 滚动更新（v1 → v2）

```bash
# 修改 src/main.py 的 APP_VERSION
docker build -t k8s-local-stack:v2 .
minikube image load k8s-local-stack:v2
kubectl -n k8s-demo set image deploy/k8s-local-stack-deploy app=k8s-local-stack:v2
kubectl -n k8s-demo rollout status deploy/k8s-local-stack-deploy

# 回滚
kubectl -n k8s-demo rollout undo deploy/k8s-local-stack-deploy
```

### 2. ConfigMap 热更新

```bash
kubectl -n k8s-demo edit cm app-config
# 修改 LOG_LEVEL 从 info → debug，保存
# 等 60s
curl http://localhost:8000/config  # 反映变更
```

### 3. 自愈演示

```bash
POD=$(kubectl -n k8s-demo get pod -l app=k8s-local-stack -o jsonpath='{.items[0].metadata.name}')
kubectl -n k8s-demo exec -it $POD -- curl http://localhost:8000/crash
kubectl -n k8s-demo get pods -w    # 看新 Pod 拉起
```

### 4. 负载均衡

```bash
for i in {1..10}; do curl -s http://localhost:8000/ | python3 -c "import json,sys; print(json.load(sys.stdin)['hostname'])"; done
# 看到不同 Pod 主机名
```

## 清理

```bash
kubectl delete -f k8s/
docker rmi k8s-local-stack:v1 k8s-local-stack:v2
minikube stop
```

## 面试要点

- **多阶段构建**：节省 40% 镜像体积，非 root 用户运行
- **健康探针**：startupProbe 给慢启动应用宽限期，readinessProbe 失败则从 Service 摘除
- **资源限制**：requests 用于调度决策，limits 防止资源耗尽
- **配置外置**：ConfigMap 注入避免重打镜像，Volume 挂载支持热更新
- **Secret**：base64 编码 ≠ 加密，生产应启用 EncryptionConfiguration
- **滚动更新**：maxSurge + maxUnavailable 控制更新速度，默认不中断服务