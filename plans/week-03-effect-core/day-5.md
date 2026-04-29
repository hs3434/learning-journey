# Day 5：SSE/WebSocket 概念引入

## 今日目标
理解流式输出的基本概念，为 Week 5-6 深度学习 SSE 铺垫

## 学习资料

### 英文（主要）
- [Server-Sent Events MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [WebSocket MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

### 中文（辅助）
- [SSE vs WebSocket 对比](https://juejin.cn/post/684490360)

## 理论学习（1小时）

### Server-Sent Events (SSE)
```javascript
// 服务器端（Node.js）
res.writeHead(200, {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive'
});

res.write('data: {"content":"Hello"}\n\n');
res.write('data: {"content":"World"}\n\n');

// 客户端
const eventSource = new EventSource('/stream');
eventSource.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

### WebSocket
```javascript
// 服务器端
import { WebSocketServer } from 'ws';
const wss = new WebSocketServer({ port: 8080 });

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    console.log('received:', data.toString());
    ws.send('echo: ' + data.toString());
  });
});

// 客户端
const ws = new WebSocket('ws://localhost:8080');
ws.onopen = () => ws.send('hello');
ws.onmessage = (event) => console.log(event.data);
```

### SSE vs WebSocket 对比

| 特性 | SSE | WebSocket |
|------|-----|-----------|
| 方向 | 单向（服务端→客户端） | 双向 |
| 连接 | HTTP/1.1（简化） | 独立协议 |
| 重连 | 自动 | 手动处理 |
| 二进制 | 需要编码 | 原生支持 |
| 适用场景 | 推送、通知、流式输出 | 实时游戏、聊天 |

## 练手项目（1.5小时）

### 项目：Week3 Effect LLM - SSE 流式调用初探

**需求**：

```typescript
// src/stream.ts
export async function* streamSSE(url: string, body: object): AsyncGenerator<string> {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.body) {
    throw new Error('No response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        yield data;
      }
    }
  }
}

// Effect 包装
import { Effect } from 'effect';

export const streamLLM = (
  request: LLMRequest
): Effect.Effect<AsyncGenerator<string, void, never>, Error, never> =>
  Effect.sync(() => streamSSE('https://api.openai.com/v1/chat/completions', {
    ...request,
    stream: true
  }));

// 使用
const generator = await Effect.runPromise(streamLLM({ model: 'gpt-4', messages: [] }));
for await (const chunk of generator) {
  console.log('Received:', chunk);
}
```

**Scaffolding**：

```typescript
// projects/week-03-effect-llm/src/stream.ts
export async function* streamSSE(url: string, body: object): AsyncGenerator<string> {
  // TODO: 实现 SSE 流式读取
  // 1. fetch 请求
  // 2. 读取 response.body
  // 3. 逐行解析 data: 前缀
  // 4. yield 每条消息
}

import { Effect } from 'effect';

export const streamLLM = (request: LLMRequest): Effect.Effect<AsyncGenerator<string>, Error, never> =>
  // TODO: Effect.sync 包装
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-03-effect-llm
# 需要有一个 SSE 测试服务器
npx tsx src/stream.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现 streamSSE 生成器
- [ ] 用 Effect.sync 包装
- [ ] 理解 SSE 和 WebSocket 的区别
- [ ] 理解流式输出的使用场景
- [ ] 无编译错误
