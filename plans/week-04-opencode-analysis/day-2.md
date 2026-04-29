# Day 2：OpenCode 目录结构与核心模块

## 今日目标
理解 OpenCode 的模块划分、核心入口、依赖注入架构

## 学习资料

### 英文（主要）
- [OpenCode Architecture](https://github.com/anomalyco/opencode/tree/main/docs/architecture.md)（如果有）

### 中文（辅助）
- 源码根目录的 README.md

## 理论学习（1小时）

### 目录结构分析
```
opencode/
├── packages/
│   ├── core/                 # 核心
│   │   ├── src/
│   │   │   ├── index.ts      # 导出
│   │   │   ├── config/        # 配置管理
│   │   │   ├── services/      # 服务层（用 Effect）
│   │   │   ├── adapters/      # 适配器接口
│   │   │   └── ...
│   │   └── package.json
│   │
│   ├── adapters/             # 模型适配器
│   │   ├── openai/
│   │   │   └── src/index.ts  # OpenAI 兼容 API
│   │   └── anthropic/
│   │
│   └── ui/                   # Electron 界面
│
├── apps/
│   └── desktop/
│       ├── src/
│       │   ├── main.ts       # Electron 主进程
│       │   ├── preload.ts    # 预加载脚本
│       │   └── renderer/     # React 渲染进程
│       └── package.json
```

### 核心概念
```typescript
// packages/core/src/index.ts 导出
export { Config, ConfigLayer } from './config/';
export { LLMService, LLMLayer } from './services/llm';
export { ModelAdapter } from './adapters/';

// packages/core/src/services/llm.ts
// 使用 Effect Layer 管理服务依赖
```

### 配置文件加载
```typescript
// packages/core/src/config/loader.ts
// 优先级：命令行 > 环境变量 > 配置文件

const configLoader = Effect.gen(function* () {
  // 1. 加载默认配置
  const defaults = yield* loadDefaults();

  // 2. 加载 .env
  const env = yield* loadEnv();

  // 3. 加载配置文件
  const file = yield* loadConfigFile();

  // 合并（后者覆盖前者）
  return mergeConfig(defaults, env, file);
});
```

## 练手项目（1.5小时）

### 项目：Week4 OpenCode Debug - 源码分析

**需求**：

```typescript
// 在 opencode/packages/core/src/ 下找到并阅读以下文件：

// 1. 入口文件
// index.ts 或 main.ts

// 2. 服务层（如果有）
// services/llm.ts 或 services/chat.ts

// 3. 适配器
// adapters/ 目录下的文件

// 4. 配置加载
// config/loader.ts 或 config/index.ts

// 分析内容：
// - 如何初始化 Effect Layer
// - 服务如何组织
// - 错误如何处理
```

**分析模板**：

```markdown
# OpenCode 核心模块分析

## 入口点
- 文件：
- 导出内容：

## 服务层
- 文件：
- 使用 Effect 的地方：

## 适配器
- 文件：
- 接口定义：

## 配置加载
- 文件：
- 加载顺序：

## 待深入
- 问题 1：
- 问题 2：
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd opencode
# 搜索关键模式
grep -r "Effect.gen" packages/core/src/ --include="*.ts" | head -20
grep -r "Layer" packages/core/src/ --include="*.ts" | head -20
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 找到核心入口文件
- [ ] 分析服务层架构
- [ ] 理解适配器接口
- [ ] 理解配置加载顺序
- [ ] 记录分析结果
