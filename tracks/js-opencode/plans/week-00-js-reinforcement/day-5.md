# Day 5：ES6 模块系统（import/export）

## 今日目标
掌握 ES6 模块的 import/export 语法，理解静态解析、与 CommonJS 的区别

## 学习资料

### 英文（主要）
- [MDN: import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import)
- [MDN: export](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/export)
- [Node.js ESM](https://nodejs.org/api/esm.html)

### 中文（辅助）
- [ES6 模块详解](https://juejin.cn/post/6844903420289589261)

## 理论学习（1小时）

### export
```javascript
// 命名导出
export const name = 'Alice';
export function greet() { return 'Hello'; }

// 批量导出
const age = 30;
function say() { return 'Hi'; }
export { age, say };

// 默认导出（每个文件一个）
export default function() { return 'default'; }
// 或
// export { greet as default };

// 重新导出
export { name, greet } from './other.js';
export * from './other.js';
```

### import
```javascript
// 命名导入
import { name, greet } from './module.js';

// 重命名
import { name as userName } from './module.js';

// 默认导入
import defaultExport from './module.js';

// 混合导入
import defaultExport, { name, greet as sayHi } from './module.js';

// 整体导入
import * as module from './module.js';
console.log(module.name);

// 动态导入
const module = await import('./module.js');
```

### 静态解析
```javascript
// import 是静态的（编译时解析，不能在条件语句中）
if (condition) {
  import { foo } from './module.js'; // 语法错误！
}

// 动态导入
if (condition) {
  const module = await import('./module.js');
}

// 这允许：
// 1. tree-shaking（删除未使用的导出）
// 2. 循环引用检测
// 3. 静态分析
```

### CommonJS vs ESM
```javascript
// CommonJS
const fs = require('fs');
module.exports = { foo };
exports.bar = bar;

// ESM
import fs from 'fs';
export const foo = 1;
export default obj;

// 不能在 ESM 中使用 require
// 不能在 CommonJS 中使用 import（除非转译）
```

## 练手项目（1.5小时）

### 项目：Week0 JS 基础 - 模块系统练习

**目录结构**：
```
src/modules/
├── math.js        # 数学工具
├── string.js      # 字符串工具
├── index.js        # 主入口
```

**需求**：

```javascript
// src/modules/math.js
export const PI = 3.14159;

export function add(a, b) {
  return a + b;
}

export function multiply(a, b) {
  return a * b;
}

export default function sum(...nums) {
  return nums.reduce((a, b) => a + b, 0);
}

// src/modules/string.js
export function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function truncate(str, maxLength) {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
}

// src/modules/index.js
export { PI, add, multiply, sum } from './math.js';
export { capitalize, truncate } from './string.js';
export { default as computeAll } from './math.js';

// src/index.js
import { add, multiply } from './modules/math.js';
import { capitalize, truncate } from './modules/string.js';
import sum from './modules/math.js';
import * as utils from './modules/index.js';

console.log(add(1, 2));              // 3
console.log(sum(1, 2, 3, 4));       // 10
console.log(capitalize('hello'));    // Hello
console.log(truncate('Hello World', 5)); // Hello...
```

**Scaffolding**：

```javascript
// projects/week-00-js-reinforcement/src/modules/math.js
// 导出 PI, add, multiply, 默认导出 sum

// projects/week-00-js-reinforcement/src/modules/string.js
// 导出 capitalize, truncate

// projects/week-00-js-reinforcement/src/index.js
// 导入并使用所有模块
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-00-js-reinforcement
node src/index.js
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现命名导出和默认导出
- [ ] 实现批量导出和重导出
- [ ] 正确使用 import 各种语法
- [ ] 理解 ESM 静态解析特点
- [ ] 无运行错误
