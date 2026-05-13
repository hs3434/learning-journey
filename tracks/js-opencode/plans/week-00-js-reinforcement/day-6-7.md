# Day 6-7：综合练习与 Week1 预览

## 周末目标
综合练习 Week 0 所有内容，预览 Week 1 TypeScript 内容

## 综合练习（2小时）

### 练习 1：模块化工具库
```javascript
// src/utils/
├── storage.js     # 本地存储封装
├── format.js      # 格式化工具
└── index.js       # 统一导出
```

```javascript
// src/utils/storage.js
const STORAGE_PREFIX = 'app_';

export function getItem(key, defaultValue = null) {
  const value = localStorage.getItem(STORAGE_PREFIX + key);
  if (value === null) return defaultValue;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

export function setItem(key, value) {
  const serialized = typeof value === 'string' ? value : JSON.stringify(value);
  localStorage.setItem(STORAGE_PREFIX + key, serialized);
}

export function removeItem(key) {
  localStorage.removeItem(STORAGE_PREFIX + key);
}
```

```javascript
// src/utils/format.js
export function formatDate(date, locale = 'zh-CN') {
  return new Intl.DateTimeFormat(locale).format(date);
}

export function formatNumber(num, options = {}) {
  return new Intl.NumberFormat('zh-CN', options).format(num);
}

export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}
```

### 练习 2：async 工具函数
```javascript
// src/utils/async.js

export async function retry(fn, maxAttempts = 3, delay = 1000) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxAttempts - 1) throw error;
      await new Promise(res => setTimeout(res, delay * (i + 1)));
    }
  }
}

export async function timeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), ms)
    )
  ]);
}

export function createAsyncQueue() {
  const queue = [];
  let processing = false;

  async function process() {
    if (processing || queue.length === 0) return;
    processing = true;

    while (queue.length > 0) {
      const { fn, resolve, reject } = queue.shift();
      try {
        resolve(await fn());
      } catch (e) {
        reject(e);
      }
    }

    processing = false;
  }

  return {
    add(fn) {
      return new Promise((resolve, reject) => {
        queue.push({ fn, resolve, reject });
        process();
      });
    }
  };
}
```

## Week 1 TypeScript 预览（1小时）

### 什么是 TypeScript
```typescript
// JavaScript 是动态类型语言
let x = 1;
x = 'hello'; // OK

// TypeScript 添加静态类型
let x: number = 1;
x = 'hello'; // Error: Type 'string' is not assignable to type 'number'
```

### TypeScript 优势
```typescript
// 1. 类型安全：编译时发现错误
function add(a: number, b: number): number {
  return a + b;
}

// 2. IDE 支持：智能提示、重构支持
// 3. 代码文档：类型即文档
// 4. 可维护性：改动时知道影响范围
```

### 学习路线预览
```
Week 1 目标：TypeScript 类型系统
- Day 1: 联合类型、交叉类型、泛型基础
- Day 2: 工具类型（Partial/Pick/Omit）
- Day 3: type vs interface
- Day 4: 泛型进阶
- Day 5: async/await 类型、Promise 类型
- Day 6-7: 模块化 + Week1 项目整合
```

## 调试复盘（1小时）

### 验证方式
```bash
cd projects/week-00-js-reinforcement
node src/index.js
```

### Week 0 整体回顾
```
1. 闭包和作用域：理解 JavaScript 独特的闭包机制
2. 原型链和 this：理解原型继承和 this 绑定
3. Promise 和 async：掌握异步编程
4. 事件循环：理解 JavaScript 执行模型
5. ES6 模块：掌握模块化开发
```

## 产出检查清单
- [ ] 完成 storage 工具模块
- [ ] 完成 format 工具模块
- [ ] 完成 async 工具函数
- [ ] 理解 Week 1 TypeScript 内容
- [ ] 无运行错误
