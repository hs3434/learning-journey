# Day 2：工具类型（Utility Types）、类型守卫（Type Guards）

## 今日目标
掌握 TypeScript 内置工具类型（`Partial`/`Required`/`Pick`/`Omit`/`Record`/`Readonly`），理解类型守卫实现窄化

## 学习资料

### 英文（主要）
- [TypeScript Handbook: Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [TypeScript Handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)

### 中文（辅助）
- [TypeScript 工具类型详解](https://juejin.cn/post/6844904157524197376)

## 理论学习（1小时）

### 常用工具类型

```typescript
// 1. Partial<T> - 所有属性变为可选
type PartialUser = Partial<User>;

// 2. Required<T> - 所有属性变为必选
type RequiredConfig = Required<Config>;

// 3. Pick<T, K> - 选取部分属性
type UserPreview = Pick<User, 'id' | 'name'>;

// 4. Omit<T, K> - 排除部分属性
type UserWithoutPassword = Omit<User, 'password'>;

// 5. Record<K, V> - 键值映射
type UserMap = Record<string, User>;

// 6. Readonly<T> - 只读
type FrozenConfig = Readonly<Config>;
```

### 自定义工具类型
```typescript
// 提取函数返回类型
type ReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R ? R : never;

// 提取参数类型
type Parameters<T extends (...args: any) => any> = T extends (...args: infer P) => any ? P : never;
```
- `infer R` = 自动创建临时占位变量，不需要像 `T` 一样提前申明

### 类型守卫（Type Guards）
```typescript
// 1. typeof 守卫
function isString(val: unknown): val is string {
  return typeof val === 'string';
}

// 2. in 守卫
function hasProp(obj: unknown, prop: string): obj is { [key: string]: any } {
  return typeof obj === 'object' && obj !== null && prop in obj;
}

// 3. instanceof 守卫
function isError(val: unknown): val is Error {
  return val instanceof Error;
}

// 4. 自定义类型守卫 + 联合类型窄化
function isLLMError(err: unknown): err is { type: 'api'; code: number } {
  return typeof err === 'object' && err !== null && 'type' in err && err.type === 'api';
}
```
- `===` 是严格相等运算符，用于比较两个值是否严格相等，包括类型比较。
- `==` 是相等运算符，用于比较两个值是否相等，但在比较之前会进行类型转换。
- `!==` 和 `!=` 分别是不严格不相等运算符和不相等运算符。

## 练手项目（1.5小时）

### 项目：Week1 LLM Tool - 类型守卫与工具类型

**需求**：
```typescript
// 1. 为 LLMError 添加类型守卫
function isNetworkError(err: LLMError): err is { type: 'network'; message: string } {
  // TODO
}

function isTimeoutError(err: LLMError): err is { type: 'timeout'; ms: number } {
  // TODO
}

// 2. 创建用户配置类型（用工具类型）
interface UserConfig {
  apiKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
  timeout: number;
  retries: number;
}

// 用工具类型创建变体
type PartialConfig = Partial<UserConfig>;           // 部分可选
type RequiredConfig = Required<PartialConfig>;      // 全部必选
type PublicConfig = Omit<UserConfig, 'apiKey'>;     // 排除敏感字段
type ReadonlyConfig = Readonly<UserConfig>;         // 只读

// 3. 实现一个泛型工具类型
// DeepPartial：递归地将所有嵌套对象变为可选
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
```

**Scaffolding**：
```typescript
// projects/week-01-llm-tool/src/guards.ts
// 实现类型守卫

import { LLMError } from './types';

export function isNetworkError(err: LLMError): boolean {
  // TODO
}

export function isTimeoutError(err: LLMError): boolean {
  // TODO
}

// projects/week-01-llm-tool/src/config.ts
// 配置类型变体

export interface UserConfig {
  // TODO
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-01-llm-tool
npx tsc --noEmit src/guards.ts src/config.ts
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现三个 LLMError 类型守卫
- [ ] 使用工具类型创建 4 种配置变体
- [ ] 实现 DeepPartial 工具类型
- [ ] 无编译错误
