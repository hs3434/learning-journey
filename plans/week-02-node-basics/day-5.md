# Day 5：Effect.gen 入门铺垫

## 今日目标
理解 Effect 的核心概念 `Effect.gen`，为 Week 3 深度学习打基础

## 学习资料

### 英文（主要）
- [Effect.gen 文档](https://effect.website.org/docs/introduction)
- [Effect Handbook - Gen](https://www.effect.website/docs/essentials/generated-effect)

### 中文（辅助）
- [Effect 中文入门](https://juejin.cn/post/7345863616824377356)

## 理论学习（1小时）

### Effect 是什么
```typescript
// Effect<A, E, R> 三个类型参数
// A - 成功时的输出类型
// E - 错误类型
// R - 依赖（Context）

import { Effect, Context } from 'effect';

// 成功效果
const success: Effect.Effect<string, never, never> = Effect.succeed('hello');

// 失败效果
const failure: Effect.Effect<never, Error, never> = Effect.fail(new Error('oops'));

// 使用 pipe 组合
const combined = Effect.succeed(1).pipe(
  Effect.map(n => n + 1),
  Effect.map(n => n * 2)
);
```

### Effect.gen 语法
```typescript
import { Effect, Context } from 'effect';

// async/await 的 Effect 版本
const program = Effect.gen(function* () {
  const a = yield* Effect.succeed(1);
  const b = yield* Effect.succeed(2);
  return a + b;  // => 3
});

// 支持 await 异步操作
const fetchUser = Effect.gen(function* () {
  const response = yield* Effect.promise(() => fetch('/api/user'));
  const user = yield* Effect.promise(() => response.json());
  return user;
});
```

### 关键点（记住即可）
```typescript
// 1. yield* 等同于 await，但返回的是 Effect
const result = yield* someEffect;

// 2. Effect.fail 创建一个失败效果
yield* Effect.fail(new Error('failed'));

// 3. Effect.promise 包装 Promise
yield* Effect.promise(() => someAsyncOperation());

// 4. 用 pipe 连接操作
effect.pipe(Effect.map(...), Effect.flatMap(...));
```

## 练手项目（1.5小时）

### 项目：Week2 CLI Tool - 用 Effect.gen 重构 Week1 LLM 调用

**需求**：

```typescript
// projects/week-02-cli-tool/src/effect-llm.ts
import { Effect, Context } from 'effect';
import type { LLMRequest, LLMResponse, LLMError } from '../week-01-llm-tool/src/types.js';

interface LLMConfig {
  baseUrl: string;
  apiKey: string;
}

class LLMConfig extends Context.Tag('LLMConfig') {}

const makeLLMConfig = (baseUrl: string, apiKey: string): LLMConfig =>
  LLMConfig.of({ baseUrl, apiKey });

const callLLMEffect = (request: LLMRequest): Effect.Effect<LLMResponse, LLMError, LLMConfig> =>
  Effect.gen(function* () {
    const config = yield* LLMConfig;
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
      return yield* Effect.fail({
        type: 'api' as const,
        code: response.status,
        message: response.statusText,
      });
    }

    const data = yield* Effect.promise(() => response.json() as Promise<LLMResponse>);
    return data;
  });

// 使用
const config = makeLLMConfig('https://api.openai.com/v1', process.env.OPENAI_KEY || '');
const result = await Effect.runPromise(
  Effect.provideService(callLLMEffect({ model: 'gpt-4', messages: [] }), LLMConfig, config)
);
```

**Scaffolding**：

```typescript
// projects/week-02-cli-tool/src/effect-llm.ts
import { Effect } from 'effect';

class LLMConfig extends Effect.Tag('LLMConfig') {}

const callLLMEffect = (request) => Effect.gen(function* () {
  // TODO: 用 Effect.gen 实现 LLM 调用
  // 1. 获取 config
  // 2. fetch 请求
  // 3. 错误处理返回 LLMError
  // 4. 返回 LLMResponse
});

export { callLLMEffect, makeLLMConfig };
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-02-cli-tool
npx tsx src/effect-llm.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 理解 Effect<A,E,R> 三个类型参数
- [ ] 能用 Effect.gen 写法替代 async/await
- [ ] 实现 callLLMEffect
- [ ] 理解 yield* 和 Effect.promise
- [ ] 无编译错误
