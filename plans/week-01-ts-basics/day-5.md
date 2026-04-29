# Day 5：async/await、Promise 错误传播、事件循环

## 今日目标
深入理解 Promise 链式调用、async/await 错误处理、Node.js 事件循环

## 学习资料

### 英文（主要）
- [MDN: async/await](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous/Promises)
- [Node.js Event Loop](https://nodejs.org/en/guides/event-loop-timers-and-nexttick)

### 中文（辅助）
- [JavaScript 事件循环详解](https://juejin.cn/post/6844904050541469704)
- [Promise 错误处理误区](https://juejin.cn/post/6844903796126620935)

## 理论学习（1小时）

### async/await 基础
```typescript
async function fetchData(): Promise<string> {
  const res = await fetch('/api/data');
  return res.json();
}

// await 的限制：必须在 async 函数内使用
```

### 错误传播
```typescript
// 1. try/catch（推荐）
async function safeFetch() {
  try {
    const data = await fetchData();
    return { success: true, data };
  } catch (error) {
    return { success: false, error };
  }
}

// 2. Promise.catch
fetchData().catch(err => console.error(err));

// 3. 错误类型 narrowing
try {
  await riskyOperation();
} catch (error) {
  if (error instanceof TypeError) {
    // 类型收窄
  }
}
```

### 并行 vs 串行
```typescript
// 串行：等待上一个完成
const a = await fetchA();
const b = await fetchB(); // 等 a 完成后才执行

// 并行：同时发起（推荐）
const [a, b] = await Promise.all([fetchA(), fetchB()]);

// Promise.allSettled：不怕部分失败
const results = await Promise.allSettled([fetchA(), fetchB()]);
```

###  
```
   ┌─────────────────────────────┐
   │         timers              │  setTimeout, setInterval
   │  pending callbacks          │  I/O callbacks
   │    idle, prepare            │  internal
   │        poll                 │  retrieve new I/O events
   │        check               │  setImmediate callbacks
   │     close callbacks        │  socket.on('close')
   └─────────────────────────────┘
```

**关键点**：
- `setTimeout` / `setInterval` → timers
- `setImmediate` → check phase
- `process.nextTick` → 优先于任何阶段

## 练手项目（1.5小时）

### 项目：Week1 LLM Tool - 请求封装与错误处理

**需求**：

```typescript
// 1. 实现 LLM 调用（使用 Day 4 的 Result 类型）
import { request } from './request';
import type { LLMRequest, LLMResponse, LLMError } from './types';

async function callLLM(req: LLMRequest): Promise<Result<LLMResponse, LLMError>> {
  const url = `${process.env.LLM_BASE_URL}/chat/completions`;

  const result = await request<LLMResponse>(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.LLM_API_KEY}`,
    },
    body: JSON.stringify(req),
  });

  return result;
}

// 2. 实现重试逻辑
async function withRetry<T>(
  fn: () => Promise<T>,
  retries: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === retries - 1) throw err;
      await new Promise(res => setTimeout(res, delay * (i + 1)));
    }
  }
  throw new Error('unreachable');
}

// 3. 批量请求（Promise.allSettled）
async function batchCallLLM(
  requests: LLMRequest[]
): Promise<Array<Result<LLMResponse, LLMError>>> {
  const promises = requests.map(req => callLLM(req));
  const results = await Promise.allSettled(promises);

  return results.map((r, i) => {
    if (r.status === 'fulfilled') return r.value;
    return { success: false, error: { type: 'network', message: String(r.reason) } };
  });
}
```

**Scaffolding**：
```typescript
// projects/week-01-llm-tool/src/client.ts
// LLM 调用客户端

import { request } from './request';
import type { LLMRequest, LLMResponse, LLMError } from './types';
import { Result } from './request';

export async function callLLM(req: LLMRequest): Promise<Result<LLMResponse, LLMError>> {
  // TODO: 实现
}

export async function withRetry<T>(fn: () => Promise<T>, retries?: number, delay?: number): Promise<T> {
  // TODO: 实现重试逻辑
}

export async function batchCallLLM(requests: LLMRequest[]): Promise<Array<Result<LLMResponse, LLMError>>> {
  // TODO: 实现批量调用
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-01-llm-tool
npx tsc --noEmit src/client.ts

# 如果有 mock 服务器可以测试
# LLM_BASE_URL=http://localhost:3000 LLM_API_KEY=test npx ts-node src/client.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现 callLLM 函数
- [ ] 实现 withRetry 重试逻辑
- [ ] 实现 batchCallLLM 批量调用
- [ ] 理解 Promise.allSettled 的用法
- [ ] 无编译错误
