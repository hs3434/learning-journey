# Day 1：联合类型、交叉类型、泛型基础

## 今日目标
理解 TypeScript 类型系统的核心概念：联合类型（`|`）、交叉类型（`&`）、泛型（`generics`）

## 学习资料

### 英文（主要）
- [TypeScript Handbook: Unions and Intersection Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#union-types)
- [TypeScript Handbook: Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)

### 中文（辅助）
- [TypeScript 手册中文版：联合类型与交叉类型](https://www.typescriptlang.org/zh/docs/handbook/2/everyday-types.html#联合类型)
- 掘金：TypeScript 泛型详解 [链接待补充]

## 理论学习（1小时）

### 联合类型（Union Types）
```typescript
type StringOrNumber = string | number;
type ID = string | number;
type Callback = () => void | Error;
```

**关键点**：
- `|` 分隔多个类型
- 窄化（narrowing）前只能访问所有类型的共有成员
- 函数返回值：协变
- 函数参数：逆变

### 交叉类型（Intersection Types）
```typescript
type Person = { name: string } & { age: number };
type Employee = Person & { employeeId: string };
```

**关键点**：
- `&` 合并多个类型
- 所有成员必须同时满足
- 冲突成员（同名不同类型）产生 `never`

### 泛型基础
```typescript
function identity<T>(arg: T): T {
  return arg;
}

type Container<T> = { value: T };
interface Pair<T, U> { first: T; second: U }
```

**关键点**：
- `<T>` 类型参数占位
- 调用时可显式 `identity<string>("hello");` 或推断 `identity("hello");`
- 约束（constraint）：`<T extends SomeType>`
- `interface Str = string` // 报错 interface 只能写 对象结构 函数结构 类的契约
- interface：用 extends 继承 `interface User extends User { age: number }` 不支持联合和交叉类型
- type 完全不支持重复声明合并，而同名 interface 会自动合并

## 练手项目（1.5小时）

### 项目：Week1 LLM Tool - 类型定义层

**目标**：为 LLM 调用工具建立类型定义框架

**需求**：
```typescript
// 定义 LLM 请求/响应的类型
// 包含：消息角色、模型参数、错误类型

// 1. 消息角色
type MessageRole = 'system' | 'user' | 'assistant';

// 2. 消息结构
interface Message {
  role: MessageRole;
  content: string;
  timestamp?: number;
}

// 3. LLM 请求参数（部分）
interface LLMRequest {
  model: string;
  messages: Message[];
  temperature?: number;
  max_tokens?: number;
}

// 4. LLM 响应结构
interface LLMResponse {
  content: string;
  model: string;
  usage?: { prompt_tokens: number; completion_tokens: number };
}

// 5. 错误类型（用联合类型）
type LLMError =
  | { type: 'network'; message: string }
  | { type: 'timeout'; ms: number }
  | { type: 'api'; code: number; message: string };
```

**Scaffolding**：
```typescript
// projects/week-01-llm-tool/src/types.ts
// 骨架文件，你来补全类型定义

export type MessageRole = // TODO

export interface Message {
  // TODO
}

// ... 其他定义
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-01-llm-tool
npx tsc --noEmit --ignoreConfig src/types.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 理解联合类型窄化机制
- [ ] 理解交叉类型的冲突处理（`never`）
- [ ] 能写泛型函数和泛型类型别名
- [ ] 完成 `src/types.ts` 的类型定义
- [ ] 无编译错误
