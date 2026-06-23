# Day 7: 整合项目 k8s-local-stack

## 项目目标

把 Week 1 所有学过的内容**串成一个可演示的完整项目**：
- ✅ Day 1 多阶段 Dockerfile
- ✅ Day 2 Compose（参考，可选）
- ✅ Day 3 kubectl 操作
- ✅ Day 4 Deployment + 健康探针 + 资源限制
- ✅ Day 5 Service 暴露
- ✅ Day 6 ConfigMap + Secret + Volume

**这个项目将作为简历中"基于 K8s 的 Python Web 部署"的核心展示**。

## 项目结构

```
k8s-local-stack/
├── README.md                # 项目说明 + 演示步骤
├── pyproject.toml           # Python 依赖
├── Dockerfile               # 多阶段构建
├── .dockerignore
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口（综合 Day 4-6）
│   ├── config.py            # 配置加载
│   └── api/
│       ├── __init__.py
│       └── routes.py        # 路由
└── k8s/
    ├── 00-namespace.yaml    # 独立 namespace
    ├── 10-configmap.yaml
    ├── 20-secret.yaml
    ├── 30-deployment.yaml
    ├── 40-service.yaml
    └── 50-ingress.yaml      # （可选）
```

## 端到端演示步骤

```bash
# 1. 启动 minikube
minikube start --driver=docker

# 2. 启用 Ingress 插件（可选）
minikube addons enable ingress

# 3. 构建并加载镜像
cd k8s-local-stack/
docker build -t k8s-local-stack:v1 .
minikube image load k8s-local-stack:v1

# 4. 部署
kubectl apply -f k8s/

# 5. 验证
kubectl -n k8s-demo get all
kubectl -n k8s-demo get pods -o wide
kubectl -n k8s-demo get svc
kubectl -n k8s-demo get cm,secret

# 6. 端口转发（最简方式）
kubectl -n k8s-demo port-forward svc/k8s-local-stack-svc 8000:80
# 另开终端：
curl http://localhost:8000/
curl http://localhost:8000/config
curl http://localhost:8000/health

# 7. 或用 minikube service
minikube service k8s-local-stack-svc -n k8s-demo --url

# 8. 演示滚动更新
# 修改 src/main.py，把版本号改成 v2
docker build -t k8s-local-stack:v2 .
minikube image load k8s-local-stack:v2
kubectl -n k8s-demo set image deploy/k8s-local-stack-deploy app=k8s-local-stack:v2
kubectl -n k8s-demo rollout status deploy/k8s-local-stack-deploy

# 9. 演示 ConfigMap 热更新
kubectl -n k8s-demo edit cm app-config
# 改一个值，保存
# 等 30-60s
curl http://localhost:8000/config  # 看是否更新

# 10. 演示自愈
POD=$(kubectl -n k8s-demo get pod -l app=k8s-local-stack -o jsonpath='{.items[0].metadata.name}')
kubectl -n k8s-demo exec -it $POD -- curl http://localhost:8000/crash
kubectl -n k8s-demo get pods -w    # 看新 Pod 拉起

# 11. 清理
kubectl delete -f k8s/
```

## 简历描述（直接复用）

> **k8s-local-stack**：基于 Kubernetes 的 Python Web 应用完整部署示例
> - 多阶段 Dockerfile 优化镜像体积（节省 ~40%），非 root 用户运行
> - FastAPI + 健康探针 + 资源 requests/limits 完整配置
> - ConfigMap 注入配置 + Volume 挂载 YAML 文件，支持热更新
> - Secret 注入敏感信息（演示 base64 解码）
> - Deployment 滚动更新 + 自愈 + 扩缩容
> - ClusterIP / NodePort / Headless 三种 Service 模式
> - **可现场演示**：minikube 启动 → 部署 → 滚动更新 → 回滚，全流程 < 5 分钟

## 自查清单

完成后对照检查：

- [ ] `minikube start` 成功
- [ ] 镜像构建无 warning
- [ ] Deployment 创建后 60s 内所有 Pod Ready
- [ ] `curl /` 返回 200，hostname 随 Pod 变化
- [ ] `curl /config` 返回从 ConfigMap 加载的 YAML
- [ ] 修改 ConfigMap 后 `curl /config` 反映变更
- [ ] 滚动更新 v1→v2 不中断服务
- [ ] 触发 crash 后 Pod 自愈
- [ ] README 中所有命令可一键执行
- [ ] 项目能 5 分钟内完成演示

## 提交到 GitHub

```bash
cd k8s-local-stack/
git init
git add .
git commit -m "feat: k8s local stack with multi-stage Dockerfile, FastAPI, ConfigMap, Secret, Service"
gh repo create k8s-local-stack --public --source=. --push
```

仓库 README 中加架构图（用 draw.io 画）：
- 用户 → NodePort Service → Deployment (3 Pods)
- Pod 从 ConfigMap / Secret 注入配置
- 滚动更新示意

## Week 1 复盘模板

```markdown
## Week 1 复盘
### 完成 vs 计划
- [ ] Day 1: 多阶段构建对比 + 镜像减小 XX%
- [ ] Day 2: docker compose up -d 跑通 FastAPI + Redis + PG
- [ ] Day 3: minikube 启动 + 部署第一个 Pod
- [ ] Day 4: Deployment 滚动更新 v1→v2→v1 完整跑通
- [ ] Day 5: Service 暴露 + 多副本负载均衡验证
- [ ] Day 6: ConfigMap 热更新 + Secret 解码
- [ ] Day 7: k8s-local-stack 整合项目跑通 + 推 GitHub

### 核心问题
- （写 1-3 个最大卡点）

### 下周调整
- （Week 2 重点：Ingress / StatefulSet / Helm / Job-CronJob）
```

## 面试问题准备（Week 1 涉及）

- Pod 和 Container 的区别？
- Deployment 和 ReplicaSet 的关系？
- K8s 滚动更新如何保证不中断？
- livenessProbe 和 readinessProbe 区别？
- ConfigMap 更新后 Pod 内配置会立即更新吗？
- K8s 中如何做服务发现？
- ClusterIP、NodePort、LoadBalancer 区别？
- K8s 自愈机制是什么？