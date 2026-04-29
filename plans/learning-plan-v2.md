# 学习计划 v2

> 核心目标：吃透 TS/Node/Effect → 能独立做 OpenCode 二次开发、功能优化、插件改造
> 3 个月后无缝切入 Rust 渐进学习

## 阶段一：4 周筑基（能看懂、能改 OpenCode）

### Week 1：TypeScript 强化
**目标**：补齐类型系统短板，Agent 开发全靠 TS

**每日节奏（3h）**：0.8h 理论 + 1.2h 项目 + 1h 调试复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1-2 | 联合/交叉类型、泛型、工具类型（Partial/Required/Pick/Omit） | 泛型工具函数练习 |
| 3-4 | `type` vs `interface`、声明合并、模块声明 | 简单类型体操 |
| 5 | async/await、Promise 错误传播、事件循环 | LLM 调用封装（TS+ESM） |
| 周末 | 休息 + 复盘 | 产出：Week1-llm-tool |

**Week1 配套项目**：LLM 基础调用工具
```typescript
// 封装 OpenAI 兼容请求，统一错误处理、超时、重试
// 产出可直接复制到 OpenCode 本地调试
```

---

### Week 2：Node.js 运行时 + Effect 入门铺垫
**目标**：理解 Node 运行时能力，为 Effect 打底

**每日节奏**：1h 理论 + 1h Node 实战 + 1h Effect 铺垫

| Day | 理论 | 实战 |
|-----|------|------|
| 1-2 | fs 文件读写、路径别名、ESM/CommonJS | 本地配置读写工具 |
| 3-4 | child_process/execa、进程通信、环境变量 | 命令行工具骨架 |
| 5 | Effect.gen 入门（只看这个，不要深入） | 用 Effect.gen 重构 Week1 项目 |
| 周末 | 复盘 | 产出：Week2-cli-tool |

**关键**：Week2 不要跳过 Effect.gen 铺垫，否则 Week3 直接上并发会懵

---

### Week 3：Effect 核心
**目标**：吃透 Effect<A,E,R>、结构化并发、Scope

**每日节奏**：1h 理论 + 1h 项目 + 1h 深入 + 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1-2 | Effect 核心类型、Succeed/Fail、catchTag | 错误类型安全重构 |
| 3-4 | 结构化并发（Fiber）、Scope、资源释放 | 超时+重试+资源销毁 |
| 5 | Layer 依赖注入（只看概念，不上深度） | 接入 orbitai 流式 SSE（穿插线） |
| 周末 | 复盘 | 产出：Week3-effect-llm |

**穿插线**：Day 5 开始接触 SSE/WebSocket 概念（Week5-6 会深入）

---

### Week 4：OpenCode 源码精读 + 小改
**目标**：能独立改 OpenCode 配置、修复小 Bug、新增简单能力

**每日节奏**：1h 源码 + 1.5h 改代码 + 0.5h 复盘

| Day | 任务 |
|-----|------|
| 1-2 | 克隆 OpenCode，跑通本地调试（`pnpm dev`） |
| 3-4 | 目录结构、依赖注入、Layer 架构、插件机制 |
| 5 | 找一个 small bug 练手修复（非预设问题） |
| 周末 | 复盘 + Week5 规划 |

**落地实操三选一**：
- 修复任意一个小 bug
- 新增自定义模型配置（接入 orbitai 私有接口）
- 自定义日志级别或本地缓存

---

## 阶段二：5-8 周工程化 + 插件开发

### Week 5-6：Effect 进阶 + SSE/WebSocket
**目标**：具备完整插件开发能力

**关键内容**：
- Effect Schema 校验
- Layer 深度依赖注入
- SSE 流式输出（OpenCode 模型响应核心）
- WebSocket 长连接

**配套项目**：
- OpenCode 私有模型插件（接入 orbitai）
- 本地工具插件（ufw/frp/nginx 运维命令）

---

### Week 7-8：性能调优 + 打包分发
**目标**：独立完成插件发布、跨平台打包

**关键内容**：
- Node 性能调优
- pnpm monorepo 插件发布
- 跨平台打包（Electron/Tauri）

**配套项目**：
- 会话缓存优化模块
- 个人 AI 运维助手雏形

---

## 阶段三：9-12 周全栈闭环 + Rust 铺垫

### Week 9-10：Hono 后端 + 全栈串联
**目标**：完整定制版 OpenCode 交付

**关键内容**：
- Hono 轻量后端（TS 全栈）
- 代理层给 Agent 做中转
- 私有化部署

---

### Week 11-12：Rust 前置 + 平稳过渡
**目标**：铺垫 Rust，3 个月后不割裂

**关键内容**：
- 每天 15-20min Rust 语法预览（Week6-7 开始）
- Week11-12：所有权、生命周期、Tokio 概念
- 长期路线：Web3 合约、本地安全沙箱

---

## 每日作息模板

### 方案 A（每日 3h 标准）
```
1.0h  理论学习（文档/教程）
1.2h  项目开发 + OpenCode 定制
0.8h  调试踩坑 + 复盘记录
```

### 方案 B（每日 4h 强化）
```
1.2h  理论学习
1.5h  项目开发 + OpenCode 定制
0.8h  源码精读
0.5h  Rust 碎片化预习（Week6 起）
```

---

## 复盘模板（每周结束填写）

```markdown
## WeekX 复盘

### 完成 vs 计划
-

### 核心问题
-

### 下周调整
-
```

---

## 重要资源

| 资源 | 地址 |
|------|------|
| Effect 官方文档 | https://effect.website.org/docs/introduction |
| OpenCode 源码 | https://github.com/anomalyco/opencode |
| 本地调试命令 | 见 AGENTS.md |

---

## 穿插学习线（不占主要时间）

| 时机 | 内容 | 目的 |
|------|------|------|
| Week2 Day5 | Effect.gen 铺垫 | 降低 Week3 认知跳跃 |
| Week3 Day5 | SSE/WebSocket 概念 | Week5-6 深度铺垫 |
| Week6 起 | Rust 语法预览 15min/天 | Week9 平稳过渡 |
