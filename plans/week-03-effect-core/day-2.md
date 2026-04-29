# Day 2：结构化并发、Fiber、Scope

## 今日目标
理解 Effect 的结构化并发模型、Fiber 概念、Scope 资源管理

## 学习资料

### 英文（主要）
- [Effect - Fibers](https://www.effect.website.org/docs/essentials/fibers)
- [Effect - Scopes](https://www.effect.website.org/docs/essentials/scopes)

### 中文（辅助）
- [Effect 并发模型详解](https://juejin.cn/post/735315336)

## 理论学习（1小时）

### Fiber 是什么
```typescript
import { Effect, Fiber } from 'effect';

// fork：启动后台 fiber
const backgroundTask = Effect.gen(function* () {
  yield* Effect.sleep(1000);
  return 42;
});

const forked = Effect.fork(backgroundTask);
// forked: Effect<Fiber.Effect<number>, never, never>

// join：等待 fiber 完成
const result = yield* Effect.forkDaemon(backgroundTask);
const value = yield* Fiber.join(result);

// 并行执行
const [a, b] = yield* Effect.all([taskA, taskB]);  // 并行！
```

### Scope 资源管理
```typescript
import { Effect, Scope } from 'effect';

// acquire + release 模式
const withResource = Effect.gen(function* (scope) {
  const resource = yield* acquire();  // 获取资源
  yield* Scope.addFinalizer(scope, () => release(resource));  // 注册释放
  return resource;
});

// 用 Effect.acquireRelease 简化
const withResource2 = Effect.acquireRelease(
  acquire(),
  release
);

// 在 scope 内执行
const program = Effect.scoped(withResource);
// scoped 会自动管理 scope 的生命周期
```

### 并发 + 资源组合
```typescript
const program = Effect.gen(function* (scope) {
  // 启动多个需要清理的资源
  const [conn1, conn2] = yield* Effect.all([
    Effect.acquireRelease(openConnection('db1'), closeConnection),
    Effect.acquireRelease(openConnection('db2'), closeConnection),
  ]);

  // 使用资源... 退出 scope 时自动关闭
});
```

## 练手项目（1.5小时）

### 项目：Week3 Effect LLM - 并发请求与资源管理

**需求**：

```typescript
// src/concurrent.ts
import { Effect, Fiber, Scope } from 'effect';
import { callLLM } from './client.js';
import type { LLMRequest, LLMResponse, LLMFailure } from './types';

// 并发调用多个 LLM
export const batchCallLLM = (
  requests: LLMRequest[]
): Effect.Effect<LLMResponse[], LLMFailure, never> =>
  Effect.gen(function* () {
    // 并行执行所有请求
    const fibers = yield* Effect.all(
      requests.map(req => Effect.fork(callLLM(req)))
    );

    // 等待所有 fiber 完成
    const results = yield* Effect.all(
      fibers.map(fiber => Fiber.join(fiber))
    );

    return results;
  });

// 超时控制
export const callLLMWithTimeout = (
  request: LLMRequest,
  timeoutMs: number = 30000
): Effect.Effect<LLMResponse, LLMFailure, never> =>
  Effect.gen(function* () {
    const fiber = yield* Effect.fork(callLLM(request));

    yield* Effect.sleep(timeoutMs);

    const interrupt = Fiber.interrupt(fiber);
    yield* Effect.race([
      Fiber.join(fiber),
      Effect.as(Effect.fail({ _tag: 'TimeoutError', ms: timeoutMs }), interrupt)
    ]);
  });

// 资源管理示例（数据库连接）
export const withConnection = <A, E, R>(
  acquire: Effect.Effect<Connection, E, R>,
  release: (conn: Connection) => Effect.Effect<void, never, R>,
  use: (conn: Connection) => Effect.Effect<A, E, R>
): Effect.Effect<A, E, R> =>
  Effect.acquireRelease(acquire, release).pipe(
    Effect.flatMap(use)
  );
```

**Scaffolding**：

```typescript
// projects/week-03-effect-llm/src/concurrent.ts
import { Effect, Fiber } from 'effect';
import { callLLM } from './client.js';
import type { LLMRequest, LLMResponse, LLMFailure } from './types';

export const batchCallLLM = (requests: LLMRequest[]): Effect.Effect<LLMResponse[], LLMFailure, never> =>
  Effect.gen(function* () {
    // TODO: 用 fork + Fiber.join 实现并发
  });

export const callLLMWithTimeout = (request: LLMRequest, timeoutMs: number): Effect.Effect<LLMResponse, LLMFailure, never> =>
  Effect.gen(function* () {
    // TODO: 实现超时中断
  });
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-03-effect-llm
npx tsx src/concurrent.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现 batchCallLLM 并发调用
- [ ] 实现 callLLMWithTimeout 超时控制
- [ ] 理解 Fiber.interrupt
- [ ] 理解 Effect.acquireRelease 模式
- [ ] 无编译错误
