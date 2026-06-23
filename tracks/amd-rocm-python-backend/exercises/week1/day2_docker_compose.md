# Day 2: Docker Compose 多容器编排

## 1. 什么是 Compose？

Docker Compose 是单机多容器编排工具（生产用 K8s，开发用 Compose）。一个 `compose.yml` 文件描述一组服务及其依赖关系。

AMD 平台型软件的本地开发模式就是 Compose + K8s 部署的组合。

## 2. compose.yml 核心结构

```yaml
version: "3.9"   # Compose 文件格式版本（可省略，V2 起可选）

services:        # 服务列表
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 3

volumes:
  redis-data:
```

## 3. 关键指令

### depends_on：启动顺序控制

```yaml
depends_on:
  db:
    condition: service_healthy   # 等 db 健康后才启动
```

⚠️ 注意：`depends_on` 只控制**启动顺序**，**不等待应用就绪**。需要应用层重试或 healthcheck。

### healthcheck：健康检查

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s       # 检查间隔
  timeout: 3s         # 超时
  retries: 3          # 失败重试
  start_period: 30s   # 启动宽限
```

### networks：自定义网络

Compose 默认会创建一个 bridge 网络，所有服务在同一网络下，可以**用服务名直接通信**（`redis`、`db`）。

```yaml
networks:
  backend:
    driver: bridge

services:
  app:
    networks: [backend]
  db:
    networks: [backend]
```

### volumes：数据持久化

```yaml
volumes:
  - redis-data:/data           # 命名卷（推荐）
  - ./logs:/app/logs           # 绑定挂载（开发调试用）
```

### environment vs env_file

```yaml
environment:                   # 直接写
  - DEBUG=true

env_file:                      # 引用 .env 文件
  - .env
```

## 4. 常用命令

```bash
# 启动（后台）
docker compose up -d

# 查看日志
docker compose logs -f app

# 进入容器
docker compose exec app bash

# 扩缩容（仅 Compose V2）
docker compose up -d --scale app=3

# 停止并清理
docker compose down              # 停服务、删容器、网络
docker compose down -v           # 同时删除卷
```

## 5. 实战：FastAPI + Redis + PostgreSQL

完整文件见同目录 `day2_docker_compose.yml`：
- `app`：FastAPI 服务（多阶段构建）
- `redis`：缓存
- `postgres`：数据库
- `pgadmin`（可选）：数据库管理 UI

## 6. 实战任务

```bash
# 1. 启动
docker compose up -d

# 2. 检查服务状态
docker compose ps

# 3. 测试 API
curl http://localhost:8000/             # 简单 hello
curl http://localhost:8000/health        # 健康检查
curl http://localhost:8000/redis-test    # 测 redis 连通
curl http://localhost:8000/db-test       # 测 PG 连通

# 4. 查看日志
docker compose logs app | tail -20

# 5. 进入 app 容器看环境变量
docker compose exec app env | grep -E "(REDIS|POSTGRES)"

# 6. 停掉某个服务，看 app 报错
docker compose stop redis
curl http://localhost:8000/redis-test
docker compose start redis

# 7. 清理
docker compose down -v
```

## 7. Compose 到 K8s 的迁移思路

| Compose | K8s 对应 |
|---------|----------|
| `services` | `Deployment` + `Service` |
| `ports` | `Service.spec.ports` |
| `environment` | `ConfigMap` / `Secret` + `envFrom` |
| `volumes` (命名卷) | `PersistentVolumeClaim` |
| `depends_on` | `initContainer` 或应用层重试 |
| `networks` | `Namespace` + `NetworkPolicy` |
| `healthcheck` | `livenessProbe` + `readinessProbe` |

Day 3-7 就会一步步把这个 Compose 文件迁移到 K8s。

## 参考资料

- [Compose 官方文档](https://docs.docker.com/compose/)
- [Compose file reference](https://docs.docker.com/compose/compose-file/)
- [Compose healthcheck 最佳实践](https://docs.docker.com/reference/compose-file/services/#healthcheck)