# Day 4：泛型进阶（约束、默认值、多泛型参数）

## 今日目标
掌握泛型的约束（`extends`）、默认值、多泛型参数的实战用法

## 学习资料

### 英文（主要）
- [TypeScript Handbook: Generic Constraints](https://www.typescriptlang.org/docs/handbook/2/generics.html#generic-constraints)
- [TypeScript Handbook: Generic Parameter Defaults](https://www.typescriptlang.org/docs/handbook/2/generics.html#generic-parameter-defaults)

### 中文（辅助）
- [TypeScript 泛型深度解析](https://juejin.cn/post/6910020552)

## 理论学习（1小时）

### 泛型约束（Constraints）
```typescript
// 约束类型必须有某个属性
interface HasId {
  id: string;
}

function getId<T extends HasId>(item: T): string {
  return item.id; // 现在可以访问 .id
}

// keyof 约束
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// 多重约束
interface A { a: string }
interface B { b: number }
function combine<T extends A & B>(obj: T): string {
  return obj.a + obj.b;
}
```

### 泛型默认值
```typescript
// 默认类型参数
interface Response<T = string, E = Error> {
  data: T;
  error: E | null;
}

// 使用默认
type DefaultResponse = Response;
// 等同于 Response<string, Error>

// 覆盖默认
type NumberResponse = Response<number>;
```

### 多泛型参数
```typescript
// 常见模式：Promise + Error + Context
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

// 映射类型
type MapToPromise<T> = {
  [K in keyof T]: Promise<T[K]>;
};

// 条件类型 + 泛型
type Unwrap<T> = T extends Promise<infer U> ? U : T;
type Unwrap<string | Promise<number>> = string | number;
```

## 练手项目（1.5小时）

### 项目：Week1 LLM Tool - 泛型封装请求与响应

**需求**：

```typescript
// 1. 泛型结果类型（类似 Rust 的 Result）
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

// 2. 泛型 API 请求函数
async function request<T, E = Error>(
  url: string,
  options?: RequestInit
): Promise<Result<T, E>> {
  try {
    const res = await fetch(url, options);
    const data = await res.json() as T;
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error as E };
  }
}

// 3. 约束版：消息必须是可序列化的
interface SerializedMessage {
  role: string;
  content: string;
}

function sendMessages<T extends SerializedMessage>(
  messages: T[]
): Promise<Result<LLMResponse>> {
  // 实现
}

// 4. 多泛型：分页响应
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

async function fetchPaginated<T>(
  url: string,
  page: number = 1,
  pageSize: number = 20
): Promise<Result<PaginatedResponse<T>>> {
  // 实现
}
```

**Scaffolding**：
```typescript
// projects/week-01-llm-tool/src/request.ts
// 泛型请求封装

export type Result<T, E = Error> = // TODO

export async function request<T, E>(url: string, options?: RequestInit): Promise<Result<T, E>> {
  // TODO: 实现 try/catch 逻辑
}

// projects/week-01-llm-tool/src/pagination.ts
// 分页类型和函数

export interface PaginatedResponse<T> {
  // TODO
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-01-llm-tool
npx tsc --noEmit src/request.ts src/pagination.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现 Result 类型
- [ ] 实现泛型 request 函数
- [ ] 实现分页响应类型和函数
- [ ] 理解泛型约束在序列化中的应用
- [ ] 无编译错误
