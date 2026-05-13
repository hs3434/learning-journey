# Day 1：Effect 核心类型、Succeed/Fail、catchTag

## 今日目标
掌握 Effect 的三种基本效果：成功、失败、依赖

## 学习资料

### 英文（主要）
- [Effect - Getting Started](https://effect.website.org/docs/introduction)
- [Effect - Succeed and Fail](https://www.effect.website/docs/essentials/succeed-and-fail)

### 中文（辅助）
- [Effect 中文教程](https://juejin.cn/post/7345863616824377356)

## 理论学习（1小时）

### Effect 三个类型参数
```typescript
// Effect<A, E, R>
// A - 成功值类型
// E - 错误类型
// R - 依赖（Context）类型

import { Effect } from 'effect';

// 成功：never 表示不会失败
const success: Effect.Effect<string, never, never> = Effect.succeed('hello');

// 失败：never 表示不关心成功值
const failure: Effect.Effect<never, Error, never> = Effect.fail(new Error('failed'));

// 有依赖：noInfer 防止类型推导问题
const withDeps: Effect.Effect<string, Error, { config: Config }> =
  Effect.succeed('hello');
```

### 基本操作
```typescript
import { Effect, Context } from 'effect';

// map：转换成功值
const doubled = Effect.succeed(5).pipe(
  Effect.map(n => n * 2)  // Effect<10, never, never>
);

// mapError：转换错误
const withError = Effect.fail('oops').pipe(
  Effect.mapError(msg => new Error(msg))  // Effect<never, Error, never>
);

// flatMap：链式调用
const chained = Effect.succeed(5).pipe(
  Effect.flatMap(n => Effect.succeed(n + 1)),
  Effect.flatMap(n => Effect.succeed(n * 2))  // Effect<12, never, never>
);
```

### catchTag 错误处理
```typescript
import { Effect, Either, Cause } from 'effect';

// catchTag：只捕获特定标签的错误
const caught = Effect.fail({ _tag: 'NetworkError', message: 'timeout' }).pipe(
  Effect.mapError({
    NetworkError: (e) => new Error(`Network failed: ${e.message}`),
    ApiError: (e) => new Error(`API failed: ${e.code}`)
  })
);

// 转换为 Either（不抛错）
const either = Effect.either(effect);
const right: Either.Either<string, Error> = either;  // Left = 错误，Right = 成功
```

## 练手项目（1.5小时）

### 项目：Week3 Effect LLM - 错误类型安全重构

**目标**：用 Effect 重构 Week1 的 LLM 调用，实现类型安全的错误处理

**需求**：

```typescript
// src/types.ts
import { Effect } from 'effect';

export interface LLMRequest {
  model: string;
  messages: Array<{ role: string; content: string }>;
  temperature?: number;
  max_tokens?: number;
}

export interface LLMResponse {
  content: string;
  model: string;
}

// 错误类型（用联合类型标签）
export type LLMFailure =
  | { _tag: 'NetworkError'; message: string }
  | { _tag: 'TimeoutError'; ms: number }
  | { _tag: 'ApiError'; code: number; message: string }
  | { _tag: 'ParseError'; message: string };

// src/client.ts
import { Effect } from 'effect';
import type { LLMRequest, LLMResponse, LLMFailure } from './types';

export const callLLM = (request: LLMRequest): Effect.Effect<LLMResponse, LLMFailure, never> =>
  Effect.gen(function* () {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    try {
      const response = yield* Effect.promise(() =>
        fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.OPENAI_KEY || ''}`,
          },
          body: JSON.stringify(request),
          signal: controller.signal,
        })
      );

      clearTimeout(timeout);

      if (!response.ok) {
        return yield* Effect.fail({
          _tag: 'ApiError',
          code: response.status,
          message: response.statusText,
        });
      }

      const data = yield* Effect.promise(() => response.json() as Promise<LLMResponse>);
      return data;
    } catch (error) {
      clearTimeout(timeout);
      if (error instanceof Error && error.name === 'AbortError') {
        return yield* Effect.fail({ _tag: 'TimeoutError', ms: 30000 });
      }
      return yield* Effect.fail({ _tag: 'NetworkError', message: String(error) });
    }
  });

// src/error-handlers.ts
import { Effect, Cause } from 'effect';
import type { LLMFailure } from './types';

export const handleLLMError = (failure: LLMFailure): Effect.Effect<string, never, never> =>
  Effect.match({
    onFailure: (f) => {
      switch (f._tag) {
        case 'NetworkError':
          return `Network error: ${f.message}`;
        case 'TimeoutError':
          return `Request timeout after ${f.ms}ms`;
        case 'ApiError':
          return `API error ${f.code}: ${f.message}`;
        case 'ParseError':
          return `Parse error: ${f.message}`;
      }
    },
    onSuccess: (data) => data.content,
  });
```

**Scaffolding**：

```typescript
// projects/week-03-effect-llm/src/types.ts
// LLM 类型和错误定义

export interface LLMRequest {
  // TODO
}

export interface LLMResponse {
  // TODO
}

export type LLMFailure =
  | { _tag: 'NetworkError'; message: string }
  | { _tag: 'TimeoutError'; ms: number }
  | { _tag: 'ApiError'; code: number; message: string };

// projects/week-03-effect-llm/src/client.ts
// Effect 版 LLM 调用

import { Effect } from 'effect';
import type { LLMRequest, LLMResponse, LLMFailure } from './types';

export const callLLM = (request: LLMRequest): Effect.Effect<LLMResponse, LLMFailure, never> =>
  Effect.gen(function* () {
    // TODO: 实现 fetch + 错误处理
  });
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-03-effect-llm
npx tsx src/client.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 定义 LLMFailure 错误联合类型
- [ ] 实现 callLLM（Effect 版）
- [ ] 实现错误处理函数
- [ ] 理解 Succeed/Fail/map/mapError
- [ ] 无编译错误
