# Day 3：Layer 依赖注入、Context

## 今日目标
掌握 Effect 的 Layer 依赖注入系统，实现模块化服务

## 学习资料

### 英文（主要）
- [Effect - Layers](https://www.effect.website.org/docs/essentials/layers)
- [Effect - Context](https://www.effect.website.org/docs/essentials/context)

### 中文（辅助）
- [Effect Layer 详解](https://juejin.cn/post/735454720)

## 理论学习（1小时）

### Context Tag
```typescript
import { Effect, Context } from 'effect';

// 定义服务 Tag
class Database extends Context.Tag('Database')<
  Database,
  { query: (sql: string) => Effect.Effect<Row[], Error, never> }
>() {}

class Logger extends Context.Tag('Logger')<
  Logger,
  { log: (msg: string) => Effect.Effect<void, never, never> }
>() {}
```

### Layer 定义
```typescript
import { Effect, Layer } from 'effect';

// 实现服务
const databaseLive = Layer.succeed(Database, {
  query: (sql) => Effect.succeed([{ id: 1, name: 'test' }])
});

const loggerLive = Layer.succeed(Logger, {
  log: (msg) => Effect.sync(() => console.log(msg))
});

// 组合多个 Layer
const serviceLayer = Layer.provideMerge(databaseLive, loggerLive);

// 使用服务
const program = Effect.gen(function* () {
  const db = yield* Database;
  const logger = yield* Logger;

  yield* logger.log('Starting...');
  const rows = yield* db.query('SELECT * FROM users');
  return rows;
});
```

### Layer 进阶
```typescript
// 带依赖的 Layer
const configLayer = Layer.effect(
  Config,
  Effect.map(reader, config => ({ config }))
);

// 替换服务（测试时）
const mockDatabase = Layer.succeed(Database, {
  query: () => Effect.succeed([{ id: 999, name: 'mock' }])
});

// 使用 mock 运行
const testProgram = Effect.provide(program, mockDatabase);
```

## 练手项目（1.5小时）

### 项目：Week3 Effect LLM - Layer 重构

**需求**：

```typescript
// src/services/config.ts
import { Effect, Context } from 'effect';

interface LLMConfig {
  baseUrl: string;
  apiKey: string;
  timeout: number;
}

class LLMConfig extends Context.Tag('LLMConfig')<LLMConfig, LLMConfig>() {}

export { LLMConfig };

// src/services/logger.ts
class AppLogger extends Context.Tag('AppLogger')<
  AppLogger,
  { info: (msg: string) => Effect.Effect<void, never, never>;
    error: (msg: string, e?: Error) => Effect.Effect<void, never, never> }
>() {}

export { AppLogger };

// src/services/llm.ts
import { Effect } from 'effect';
import { LLMConfig } from './config.js';
import { AppLogger } from './logger.js';
import type { LLMRequest, LLMResponse, LLMFailure } from '../types.js';

export const callLLM = (request: LLMRequest): Effect.Effect<LLMResponse, LLMFailure, LLMConfig | AppLogger> =>
  Effect.gen(function* () {
    const config = yield* LLMConfig;
    const logger = yield* AppLogger;

    logger.info(`Calling LLM: ${request.model}`);

    const response = yield* Effect.promise(() =>
      fetch(`${config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${config.apiKey}`,
        },
        body: JSON.stringify(request),
      })
    );

    if (!response.ok) {
      return yield* Effect.fail({ _tag: 'ApiError', code: response.status, message: response.statusText });
    }

    return yield* Effect.promise(() => response.json() as Promise<LLMResponse>);
  });

// src/layers.ts
import { Effect, Layer } from 'effect';
import { LLMConfig, AppLogger } from './services/index.js';

export const configLayer = Layer.succeed(LLMConfig, {
  baseUrl: process.env.LLM_BASE_URL || 'https://api.openai.com/v1',
  apiKey: process.env.LLM_API_KEY || '',
  timeout: 30000,
});

export const loggerLayer = Layer.succeed(AppLogger, {
  info: (msg) => Effect.sync(() => console.log(`[INFO] ${msg}`)),
  error: (msg, e) => Effect.sync(() => console.error(`[ERROR] ${msg}`, e)),
});

export const serviceLayer = Layer.merge(configLayer, loggerLayer);
```

**Scaffolding**：

```typescript
// projects/week-03-effect-llm/src/services/config.ts
class LLMConfig extends Context.Tag('LLMConfig')() {}
// TODO: 导出类型和 Layer

// projects/week-03-effect-llm/src/services/llm.ts
export const callLLM = (request: LLMRequest): Effect.Effect<LLMResponse, LLMFailure, LLMConfig | AppLogger> =>
  Effect.gen(function* () {
    // TODO: 使用 LLMConfig 和 AppLogger
  });

// projects/week-03-effect-llm/src/layers.ts
export const serviceLayer = Layer.merge(/* TODO */);
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-03-effect-llm
npx tsx src/services/llm.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 定义 LLMConfig 和 AppLogger Tag
- [ ] 实现 callLLM 使用依赖
- [ ] 创建 Layer 配置
- [ ] 用 Layer.provide 运行程序
- [ ] 无编译错误
