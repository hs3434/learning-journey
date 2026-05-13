# Day 4：Effect Schema 校验

## 今日目标
掌握 Effect 的 Schema 定义和数据校验

## 学习资料

### 英文（主要）
- [Effect Schema](https://www.effect.website.org/docs/schema)
- [effect/schema API](https://effect.website.org/docs/schema/api)

### 中文（辅助）
- [Effect Schema 入门](https://juejin.cn/post/735555555)

## 理论学习（1小时）

### Schema 定义
```typescript
import { Schema } from 'effect';

// 基础类型
const stringSchema = Schema.string;
const numberSchema = Schema.Number;
const booleanSchema = Schema.boolean;

// 结构体
const UserSchema = Schema.Struct({
  id: Schema.string,
  name: Schema.string,
  age: Schema.Number,
  email: Schema.string
});

// 可选字段
const UserWithOptionalEmail = Schema.Struct({
  id: Schema.string,
  name: Schema.string,
  email: Schema.optional(Schema.string)
});

// 联合类型
const StatusSchema = Schema.Union(
  Schema.Literal('active'),
  Schema.Literal('inactive'),
  Schema.Literal('pending')
);
```

### 校验与转换
```typescript
import { Schema, Effect } from 'effect';

// 解析（验证 + 转换）
const parseUser = Schema.parse(UserSchema);

const result = await Effect.runPromise(
  parseUser({ id: '1', name: 'Alice', age: 25 })
);
// 成功：{ id: '1', name: 'Alice', age: 25 }

const failed = await Effect.runPromise(
  parseUser({ id: 1, name: 'Alice', age: '25' })  // 类型错误
);
// 失败：ValidationError

// 解码（从 JSON API 响应转换）
const ApiResponseSchema = Schema.Struct({
  data: Schema.string,
  status: Schema.Number
});

const decode = Schema.decode(ApiResponseSchema);
```

### 复杂 schema
```typescript
// 数组
const ArraySchema = Schema.Array(Schema.string);

// 字典
const DictSchema = Schema.Record(Schema.string, Schema.Number);

// 元组
const TupleSchema = Schema.Tuple(Schema.string, Schema.Number, Schema.boolean);

// 解析后验证
const NonEmptyString = Schema.string.pipe(
  Schema.filter(s => s.length > 0, { message: () => 'Expected non-empty string' })
);
```

## 练手项目（1.5小时）

### 项目：Week3 Effect LLM - Schema 验证请求

**需求**：

```typescript
// src/schema.ts
import { Schema } from 'effect';

// Message schema
const MessageSchema = Schema.Struct({
  role: Schema.Union(Schema.Literal('system'), Schema.Literal('user'), Schema.Literal('assistant')),
  content: Schema.string
});

// LLM Request schema
const LLMRequestSchema = Schema.Struct({
  model: Schema.string,
  messages: Schema.Array(MessageSchema),
  temperature: Schema.optional(Schema.Number),
  max_tokens: Schema.optional(Schema.Number)
});

// LLM Response schema
const UsageSchema = Schema.Struct({
  prompt_tokens: Schema.Number,
  completion_tokens: Schema.Number,
  total_tokens: Schema.Number
});

const LLMResponseSchema = Schema.Struct({
  id: Schema.string,
  model: Schema.string,
  content: Schema.string,
  usage: Schema.optional(UsageSchema)
});

// 解析函数
export const parseLLMRequest = Schema.parse(LLMRequestSchema);
export const parseLLMResponse = Schema.parse(LLMResponseSchema);

// 用在 client 里
import { Effect } from 'effect';
import { Schema } from 'effect';
import { parseLLMRequest, parseLLMResponse } from './schema.js';

export const callLLM = (request: unknown): Effect.Effect<LLMResponse, LLMFailure, never> =>
  Effect.gen(function* () {
    // 先验证输入
    const validated = yield* Schema.decode(LLMRequestSchema)(request);

    const response = yield* Effect.promise(() =>
      fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.OPENAI_KEY || ''}`,
        },
        body: JSON.stringify(validated),
      })
    );

    const data = yield* Effect.promise(() => response.json());
    // 验证输出
    return yield* Schema.decode(LLMResponseSchema)(data);

  }).pipe(
    Effect.mapError(e => ({ _tag: 'ParseError', message: String(e) }))
  );
```

**Scaffolding**：

```typescript
// projects/week-03-effect-llm/src/schema.ts
import { Schema } from 'effect';

const MessageSchema = Schema.Struct({
  // TODO: role 和 content
});

const LLMRequestSchema = Schema.Struct({
  // TODO: model, messages, 可选 temperature, max_tokens
});

const LLMResponseSchema = Schema.Struct({
  // TODO: id, model, content, 可选 usage
});

export const parseLLMRequest = // TODO
export const parseLLMResponse = // TODO
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-03-effect-llm
npx tsx src/schema.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 定义 MessageSchema
- [ ] 定义 LLMRequestSchema（含可选字段）
- [ ] 定义 LLMResponseSchema
- [ ] 在 callLLM 中使用 Schema 验证
- [ ] 无编译错误
