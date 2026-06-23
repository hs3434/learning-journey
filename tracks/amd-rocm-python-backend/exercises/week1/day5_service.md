# Day 5: Service — 集群内服务发现与负载均衡

## 1. 为什么需要 Service？

Pod 是**临时的**：
- 重启后 IP 变
- 副本增减 IP 集合变
- 多副本需要一个稳定入口

**Service** = 一组 Pod 的**稳定访问入口**（虚拟 IP + 端口），通过 label selector 关联后端 Pod。

## 2. Service 类型对比

| 类型 | 作用范围 | 适用场景 |
|------|----------|----------|
| **ClusterIP**（默认）| 集群内部 | 微服务内部调用（最常用）|
| **NodePort** | 集群外（每个 Node 暴露同一端口）| 开发测试、本地访问 |
| **LoadBalancer** | 云厂商负载均衡器 | 生产环境（需云厂商支持）|
| **ExternalName** | CNAME 代理 | 代理集群外服务（如 RDS）|
| **Headless**（`clusterIP: None`）| 无虚拟 IP，DNS 直接解析 Pod IP | StatefulSet、自定义负载均衡 |

## 3. ClusterIP 示例

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-svc
spec:
  type: ClusterIP
  selector:
    app: fastapi              # ← 匹配 Pod label
  ports:
  - port: 80                  # Service 端口
    targetPort: 8000          # Pod 端口
    protocol: TCP
    name: http
```

集群内访问：`http://fastapi-svc:80` 或 `http://fastapi-svc.default.svc.cluster.local:80`

## 4. NodePort 示例

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-nodeport
spec:
  type: NodePort
  selector:
    app: fastapi
  ports:
  - port: 80
    targetPort: 8000
    nodePort: 30080            # 范围 30000-32767
```

集群外访问：`http://<任意NodeIP>:30080`

## 5. LoadBalancer 示例

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-lb
spec:
  type: LoadBalancer
  selector:
    app: fastapi
  ports:
  - port: 80
    targetPort: 8000
```

云厂商会自动创建 LB 并分配公网 IP。minikube 用 `minikube tunnel` 模拟。

## 6. 工作原理

### kube-proxy 与 iptables/IPVS

- Service 有一个**虚拟 IP**（ClusterIP）
- kube-proxy 在每个 Node 上维护 iptables 规则，把访问 ClusterIP 的流量 DNAT 到后端 Pod
- 负载均衡：默认**随机**选 Pod（iptables mode）

### Endpoints / EndpointSlice

```bash
kubectl get endpoints fastapi-svc
# NAME          ENDPOINTS                            AGE
# fastapi-svc   10.244.0.5:8000,10.244.0.6:8000,...  5m
```

readinessProbe 失败的 Pod 会**自动从 Endpoints 摘除**。

## 7. Headless Service（StatefulSet 配合）

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
spec:
  clusterIP: None              # ← Headless
  selector:
    app: postgres
  ports:
  - port: 5432
```

DNS 查询 `postgres-headless-0.postgres-headless.default.svc.cluster.local` 直接解析到具体 Pod IP。

## 8. 实战：NodePort 暴露 FastAPI

```bash
# 1. 部署 Day 4 的 Deployment（如果还没部署）
kubectl apply -f day4_deployment.yaml

# 2. 创建 Service
kubectl apply -f day5_service.yaml

# 3. 查看
kubectl get svc
kubectl get endpoints fastapi-svc
kubectl describe svc fastapi-svc

# 4. 集群内访问测试
kubectl run curl-test --image=curlimages/curl -it --rm -- sh
# 容器内：
#   curl http://fastapi-svc/
#   curl http://fastapi-svc/health
#   多访问几次，看 hostname 是否变化（负载均衡）
#   exit

# 5. 集群外访问（minikube）
minikube service fastapi-nodeport --url
# 或者
minikube ip            # 拿到 NodeIP
curl http://$(minikube ip):30080/

# 6. 触发某个 Pod 崩溃，验证 Service 自动摘除
POD=$(kubectl get pod -l app=fastapi -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD -- curl http://localhost:8000/crash
# 立即查看 endpoints，少一个 IP
kubectl get endpoints fastapi-svc -w

# 7. 清理
kubectl delete -f day5_service.yaml
kubectl delete -f day4_deployment.yaml
```

## 9. K8s DNS

K8s 集群内 DNS（CoreDNS）会自动为 Service 创建 A 记录：

- `fastapi-svc` → ClusterIP（同一个 namespace）
- `fastapi-svc.default.svc.cluster.local` → ClusterIP（FQDN）
- `_tcp.fastapi-svc.default.svc.cluster.local` → SRV 记录（端口信息）

跨 namespace 访问：`http://<svc-name>.<namespace>.svc.cluster.local:80`

## 10. Session Affinity（会话保持）

默认是随机负载均衡。如果需要 sticky session：

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800      # 3 小时
```

⚠️ AMD 平台型软件一般**不需要** session affinity，WebSocket 长连接场景才考虑。

## 11. 实战任务

1. ✅ 创建 ClusterIP Service，集群内用 curl 测试
2. ✅ 创建 NodePort Service，从 minikube IP 外部访问
3. ✅ 连续请求 10 次，记录 hostname 变化（验证负载均衡）
4. ✅ 触发 Pod 崩溃，验证 Endpoints 自动更新
5. ✅ 扩容到 5 副本，验证 Endpoints 自动扩展
6. ✅ 缩容到 1 副本，验证 Service 仍可用

## 参考资料

- [Service 官方文档](https://kubernetes.io/zh-cn/docs/concepts/services-networking/service/)
- [Service 发布类型](https://kubernetes.io/zh-cn/docs/concepts/services-networking/service/#publishing-services-service-types)
- [K8s DNS](https://kubernetes.io/zh-cn/docs/concepts/services-networking/dns-pod-service/)