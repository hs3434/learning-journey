# Day 4：模型适配器与剪贴板模块

## 今日目标
深入理解模型适配器接口和剪贴板交互模块

## 学习资料

### 英文（主要）
- [OpenCode Adapters](https://github.com/anomalyco/opencode/tree/main/packages/adapters)

### 中文（辅助）
- 查看 packages/adapters 目录

## 理论学习（1小时）

### 模型适配器接口（推测）
```typescript
// packages/adapters/src/types.ts

export interface ModelAdapter {
  name: string;
  version: string;

  // 补全请求
  complete(params: CompleteParams): Effect.Effect<CompleteResult, CompleteError, R>;

  // 流式补全
  completeStream(params: CompleteParams): Effect.Effect<StreamResult, CompleteError, R>;

  // 健康检查
  healthCheck(): Effect.Effect<boolean, Error, R>;
}

export interface CompleteParams {
  prompt: string;
  model: string;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
}

export interface CompleteResult {
  content: string;
  model: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export type CompleteError =
  | { _tag: 'NetworkError'; message: string }
  | { _tag: 'AuthError'; message: string }
  | { _tag: 'RateLimitError'; retryAfter: number }
  | { _tag: 'ApiError'; code: number; message: string };
```

### 剪贴板模块（推测）
```typescript
// packages/core/src/services/clipboard.ts

import { Effect } from 'effect';

export interface ClipboardService {
  write(text: string): Effect.Effect<void, ClipboardError, never>;
  read(): Effect.Effect<string, ClipboardError, never>;
}

export type ClipboardError =
  | { _tag: 'NotSupported'; message: string }
  | { _tag: 'WriteError'; message: string }
  | { _tag: 'ReadError'; message: string };

// Electron 实现（packages/core/src/services/clipboard.electron.ts）
export const electronClipboard: ClipboardService = {
  write: (text) => Effect.sync(() => clipboard.writeText(text)),
  read: () => Effect.sync(() => clipboard.readText()),
};
```

## 练手项目（1.5小时）

### 项目：Week4 OpenCode Debug - 模块深入

**需求**：

```bash
# 1. 找到模型适配器定义
find opencode/packages/adapters -name "*.ts" | head -10
cat opencode/packages/adapters/src/index.ts 2>/dev/null || echo "Check subdirs"

# 2. 找到剪贴板实现
find opencode -name "*clipboard*" -type f 2>/dev/null

# 3. 理解适配器如何注册
grep -r "ModelAdapter\|registerAdapter" opencode/packages --include="*.ts" | head -20
```

**分析内容**：
```markdown
# 模型适配器分析

## 接口定义
-

## OpenAI 适配器实现
-

## 适配器注册机制
-

# 剪贴板模块分析

## 接口定义
-

## Electron 实现
-

## 跨平台考虑
-
```

## 调试复盘（0.5小时）

### 验证方式
```bash
# 查看适配器如何被调用
grep -r "complete\|completeStream" opencode/packages/core --include="*.ts" | head -10
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 找到模型适配器接口定义
- [ ] 分析 OpenAI 适配器实现
- [ ] 找到剪贴板模块
- [ ] 理解跨平台实现方式
- [ ] 记录分析结果
