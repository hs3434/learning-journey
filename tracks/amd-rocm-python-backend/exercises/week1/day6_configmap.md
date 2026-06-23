# Day 6: ConfigMap + Secret + Volume 挂载

## 1. 为什么需要 ConfigMap / Secret？

镜像里硬编码配置的问题：
- 不同环境（dev/staging/prod）要打不同镜像
- 配置变更要重打镜像
- 敏感信息（密码、token）泄露风险

**ConfigMap** 存**非敏感**配置（YAML/JSON/键值对）。
**Secret** 存**敏感**配置（base64 编码，K8s 1.27+ 支持 Secret 加密存储）。

## 2. ConfigMap 创建方式

### 字面量

```bash
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=APP_ENV=production
```

### 从文件

```bash
kubectl create configmap app-config --from-file=config.yaml
```

### YAML 声明

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "info"
  APP_ENV: "production"
  # 整文件挂载
  nginx.conf: |
    server {
      listen 80;
      ...
    }
```

## 3. Secret 创建方式

### 字面量

```bash
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password='S3cr3t!@#'
```

### YAML（注意：value 需 base64 编码）

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  # echo -n "admin" | base64
  username: YWRtaW4=
  # echo -n 'S3cr3t!@#' | base64
  password: UzNjcjN0IUAj
```

⚠️ **base64 不是加密**，Secret 默认只是 base64 编码，仍可在 etcd 明文读。要真正加密需启用 K8s **EncryptionConfiguration**。

## 4. 引用方式：环境变量

### 单个 key

```yaml
env:
- name: LOG_LEVEL
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: LOG_LEVEL
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-secret
      key: password
```

### 整 ConfigMap 注入

```yaml
envFrom:
- configMapRef:
    name: app-config       # ConfigMap 所有 key 变成环境变量
- secretRef:
    name: db-secret
```

## 5. 引用方式：Volume 挂载

```yaml
volumes:
- name: config-vol
  configMap:
    name: app-config        # /etc/config/<key> 文件
- name: secret-vol
  secret:
    secretName: db-secret   # /etc/secret/<key> 文件
containers:
- name: app
  volumeMounts:
  - name: config-vol
    mountPath: /etc/config
  - name: secret-vol
    mountPath: /etc/secret
```

应用读取 `/etc/config/LOG_LEVEL` 等文件即可。**配置变更时文件会自动更新**（K8s 通过 inotify 触发更新，间隔约 30-60s）。

## 6. Volume 类型总览

| 类型 | 生命周期 | 适用 |
|------|----------|------|
| `emptyDir` | Pod 存在期间 | 容器间共享临时数据 |
| `hostPath` | 节点本机 | 访问节点资源（日志、docker.sock）|
| `configMap` / `secret` | K8s 对象存在期间 | 配置 |
| `persistentVolumeClaim` (PVC) | 数据独立于 Pod | 数据库、文件存储 |
| `nfs` / `csi` | 外部存储 | 生产持久化 |

## 7. PVC（PersistentVolumeClaim）

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes:
    - ReadWriteOnce        # 单节点读写
  resources:
    requests:
      storage: 1Gi
```

```yaml
volumes:
- name: data
  persistentVolumeClaim:
    claimName: data-pvc
```

⚠️ **Deployment + PVC 有坑**：多副本 Pod 会争抢同一 PVC 绑定的 PV，**需用 StatefulSet** 才能让每个 Pod 独立 PVC。

## 8. 配置热更新

ConfigMap 更新后：
- **环境变量**：容器内的 env 不会自动更新（需重启 Pod）
- **Volume 文件**：文件内容会更新（延迟 ~30-60s）
- 实现自动 reload：应用监听文件变化（inotify）或 HTTP endpoint（`nginx -s reload`）

## 9. 实战任务

```bash
# 1. 创建 ConfigMap 和 Secret
kubectl apply -f day6_configmap.yaml
kubectl apply -f day6_secret.yaml

# 2. 验证
kubectl get cm
kubectl get secret
kubectl describe cm app-config
kubectl get secret db-secret -o yaml      # 看 base64 编码

# 3. 部署带 env 注入的 Pod
kubectl apply -f day6_pod_with_config.yaml

# 4. 进入 Pod 验证环境变量
POD=$(kubectl get pod -l app=config-demo -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD -- env | grep -E "(LOG_LEVEL|DB_)"
kubectl exec -it $POD -- ls /etc/config/
kubectl exec -it $POD -- cat /etc/config/LOG_LEVEL
kubectl exec -it $POD -- ls /etc/secret/
kubectl exec -it $POD -- cat /etc/secret/password      # base64 编码后的内容
kubectl exec -it $POD -- base64 -d /etc/secret/password  # 解码

# 5. 修改 ConfigMap（演示热更新）
kubectl edit cm app-config
# 把 LOG_LEVEL 从 info 改成 debug，保存
# 等待 60s
kubectl exec -it $POD -- cat /etc/config/LOG_LEVEL     # 应变成 debug

# 6. 用 Python 演示 Secret 解码
kubectl exec -it $POD -- python3 -c "
import base64
with open('/etc/secret/password') as f:
    encoded = f.read()
print('Decoded:', base64.b64decode(encoded).decode())
"

# 7. 清理
kubectl delete -f day6_pod_with_config.yaml
kubectl delete cm app-config
kubectl delete secret db-secret
```

## 10. 最佳实践

1. **配置外置**：所有可调参数走 ConfigMap，不硬编码到镜像
2. **敏感信息走 Secret**：密码、API Key、证书
3. **不直接 base64 编码当加密用**：生产环境启用 K8s EncryptionConfiguration + KMS
4. **配置文件优先用 Volume 挂载**：便于热更新
5. **环境变量适合一次性配置**：启动时读取，运行时不变
6. **amd-rocm 应用**：模型路径、GPU 配置、并行数都应该走 ConfigMap

## 参考资料

- [ConfigMap 官方文档](https://kubernetes.io/zh-cn/docs/concepts/configuration/configmap/)
- [Secret 官方文档](https://kubernetes.io/zh-cn/docs/concepts/configuration/secret/)
- [Volume 类型](https://kubernetes.io/zh-cn/docs/concepts/storage/volumes/)
- [配置最佳实践](https://kubernetes.io/zh-cn/docs/concepts/configuration/overview/)