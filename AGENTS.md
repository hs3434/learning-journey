# AGENTS.md

## 仓库用途

个人学习计划仓库，记录 TS/Node/Effect/OpenCode 开发的学习过程与实战项目。

## 项目结构

```
/learning-journey
├── plans/           # 学习计划文档
├── projects/        # 配套小项目代码（每周一个）
├── notes/           # 学习笔记、复盘记录
└── opencode/        # OpenCode 源码克隆（调试用）
```

## 开发环境

- Node.js 18+
- pnpm（OpenCode monorepo 使用 pnpm workspace）
- TypeScript 5.x

## 学习顺序

Week 0（JS 强化）→ Week 1（TS）→ Week 2（Node）→ Week 3（Effect 铺垫）→ Week 4（Effect 核心）→ Week 5-6（OpenCode 源码）

**关键约束**：
- Effect.gen 铺垫（Week2 Day5）不可跳过，否则 Week3 直接上并发会懵
- SSE/WebSocket 概念 Week3 Day5 提前接触，为 Week5-6 深度铺垫

## 学习计划

主计划：`plans/learning-plan-v2.md`

节奏：3-4h/天，理论:项目:调试 ≈ 1h:1.2h:0.8h

## 复盘格式（每周结束填写）

```markdown
## WeekX 复盘
### 完成 vs 计划
-
### 核心问题
-
### 下周调整
-
```

## 命令参考

```bash
# OpenCode 本地调试
git clone https://github.com/anomalyco/opencode.git opencode
cd opencode && pnpm install && pnpm build && pnpm dev

# Effect 官方文档
open https://effect.website.org/docs/introduction
```

## 重要资源

| 资源 | 地址 |
|------|------|
| Effect 官方文档 | https://effect.website.org/docs/introduction |
| OpenCode 源码 | https://github.com/anomalyco/opencode |

## 穿插学习线

| 时机 | 内容 |
|------|------|
| Week2 Day5 | Effect.gen 铺垫 |
| Week3 Day5 | SSE/WebSocket 概念 |
| Week6 起 | Rust 语法预览 15min/天 |
