# Day 6-7：Week3 项目整合与 Effect 最佳实践

## 周末目标
整合 Week3 所学，形成完整的 Effect 版 LLM 工具

## 理论补充（1小时）

### Effect 最佳实践

```typescript
// 1. 错误类型用联合类型（而非 Error）
// Good
type Failures = { _tag: 'NotFound'; id: string } | { _tag: 'Unauthorized' };

// Bad
type Failures = Error;

// 2. 用 catchTag 而非 try/catch
const handled = effect.pipe(
  Effect.mapError({
    NotFound: (e) => new UserError(`User ${e.id} not found`)
  })
);

// 3. Layer 按需组合
const fullLayer = Layer.provideMerge(
  configLayer,
  Layer.provideMerge(loggerLayer, databaseLayer)
);

// 4. 用 Effect.all 并行
const [a, b, c] = yield* Effect.all([
  fetchA(),
  fetchB(),
  fetchC()
], { concurrency: 3 });  // 限制并发数

// 5. 善用 Option 处理可选值
import { Option } from 'effect';
const name: Option.Option<string> = user.name;
```

### 项目架构参考
```
src/
├── types.ts           # 领域类型
├── schema.ts          # Schema 验证
├── services/
│   ├── config.ts      # 配置服务
│   ├── logger.ts      # 日志服务
│   └── llm.ts         # LLM 服务
├── client.ts          # 主客户端（使用服务）
├── concurrent.ts      # 并发工具
├── stream.ts          # 流式调用
└── index.ts           # 统一导出
```

## 项目整合（2小时）

### 整合要求

1. **统一导出**：所有模块通过 `index.ts` 导出
2. **类型安全**：请求/响应都用 Schema 验证
3. **依赖注入**：通过 Layer 提供配置和日志
4. **错误处理**：使用 `_tag` 联合类型
5. **可测试**：可替换 Layer 进行单元测试

```typescript
// src/index.ts
export * from './types.js';
export * from './schema.js';
export * from './services/config.js';
export * from './services/logger.js';
export * from './client.js';
export { streamLLM } from './stream.js';
export { batchCallLLM, callLLMWithTimeout } from './concurrent.js';
```

## OpenCode 中的 Effect 使用模式

### OpenCode 源码参考
```typescript
// OpenCode 中的 Effect 使用模式（简化）

// 1. 统一用 Effect.gen
const program = Effect.gen(function* () {
  const config = yield* Config;
  const model = yield* ModelAdapter;

  const response = yield* model.complete(prompt);

  yield* Logger.info(`Response: ${response.content}`);

  return response;
});

// 2. Layer 组织服务
export const MainLayer = Layer.provideMerge(
  ConfigLayer,
  Layer.provideMerge(ModelAdapterLayer, LoggerLayer)
);

// 3. 运行程序
Effect.runPromise(Effect.provide(program, MainLayer));
```

## 调试复盘（1小时）

### 验证方式
```bash
cd projects/week-03-effect-llm
npx tsx src/index.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 统一导出所有模块
- [ ] Schema 验证正常工作
- [ ] Layer 依赖注入正常
- [ ] 错误处理类型安全
- [ ] 理解 OpenCode 的 Effect 架构
