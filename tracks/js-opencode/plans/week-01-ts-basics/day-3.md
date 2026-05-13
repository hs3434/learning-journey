# Day 3：`type` vs `interface`、声明合并、模块声明

## 今日目标
理解 `type` 和 `interface` 的区别与适用场景，掌握声明合并和模块声明扩展

## 学习资料

### 英文（主要）
- [TypeScript Handbook: Interfaces](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#interfaces)
- [TypeScript Handbook: Declaration Merging](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html)

### 中文（辅助）
- [TypeScript interface vs type 详解](https://juejin.cn/post/6844904172896346125)

## 理论学习（1小时）

### `type` vs `interface` 对比

| 场景 | `type` | `interface` |
|------|--------|-------------|
| 对象形状定义 | ✅ | ✅ |
| 声明合并 | ❌ | ✅ |
| 扩展（extends） | `&` 交叉 | `extends` 关键字 |
| 计算属性 | ✅ | ❌ |
| 元组/联合类型 | ✅ | ❌ |

### 何时用哪个
```typescript
// interface：需要声明合并时（插件、扩展）
interface Window {
  analytics: Analytics;
}

// type：联合类型、元组、计算属性
type ID = string | number;
type Point = [number, number];
type Keys = 'a' | 'b' | 'c';

// 混用：interface 扩展 type
type Base = { id: string };
interface User extends Base {
  name: string;
}

// type 交叉 interface
interface A { a: string }
type B = A & { b: number };
```

### 声明合并（Declaration Merging）
```typescript
// 同一接口名会合并属性
interface User {
  name: string;
}
interface User {
  age: number;
}
// 结果：User { name: string; age: number }

// 适用于：给全局 window 扩展、给模块补充类型
```

### 模块声明（Module Augmentation）
```typescript
// 给第三方库扩展类型
declare module 'express' {
  interface Application {
    myCustomMethod(): void;
  }
}

// 使用
import express from 'express';
const app = express();
app.myCustomMethod(); // ✅
```

## 练手项目（1.5小时）

### 项目：Week1 LLM Tool - 模块扩展与类型组织

**需求**：

```typescript
// 1. 创建一个 LLM 模块，定义核心接口
// src/llm/index.ts
export interface LLMProvider {
  name: string;
  baseUrl: string;
  apiKey: string;
}

// 2. 扩展 Global Window 类型（声明合并）
// src/types/window.d.ts
interface Window {
  llmConfig?: LLMProvider;
  analytics?: Analytics;
}

// 3. 创建 Express 的模块声明扩展（如果使用）
// src/types/express.d.ts
declare module 'express' {
  interface Request {
    userId?: string;
  }
}

// 4. 组织类型导出
// src/index.ts
export * from './types';
export * from './guards';
export * from './config';
export { type LLMProvider } from './llm';
```

**Scaffolding**：
```typescript
// projects/week-01-llm-tool/src/types/window.d.ts
// 扩展 Window 类型

declare global {
  interface Window {
    // TODO: 添加 llmConfig
  }
}

export {};
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-01-llm-tool
npx tsc --noEmit
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 理解 type/interface 适用场景
- [ ] 实现 Window 类型扩展（声明合并）
- [ ] 模块声明扩展示例（Express 或其他）
- [ ] 统一导出类型
- [ ] 无编译错误
