# Day 6-7：ESM / CommonJS、路径别名、包管理

## 周末目标
掌握 Node.js 模块系统（ESM/CommonJS）、pnpm workspace 配置、路径别名设置

## 学习资料

### 英文（主要）
- [Node.js ESM](https://nodejs.org/api/esm.html)
- [pnpm workspace](https://pnpm.io/workspaces)

### 中文（辅助）
- [Node.js 模块系统详解](https://juejin.cn/post/6844903902420746254)

## 理论学习（2小时）

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
```

```javascript
// 混用注意（不推荐）
// CommonJS 中使用 ESM
// const esm = await import('./esm.mjs');

// ESM 中使用 CommonJS
// const cjs = require('./cjs'); // 不行！
```

### ESM 关键特性
```javascript
// 1. import 是静态的（编译时解析）
// 这允许 tree-shaking、循环引用检测
import { foo } from './module'; // 不能放在 if 里

// 2. dynamic import
const module = await import('./module.ts');

// 3. import.meta
import.meta.url;       // 当前文件 URL
import.meta.dirname;   // 需要 polyfill

// 4. 默认导出 vs 命名导出
export default obj;    // import obj from
export const foo;     // import { foo } from
```

### package.json 的 `type` 字段
```json
{
  "type": "module"  // .js 文件当作 ESM
  // 不写或 "commonjs" => .js 文件当作 CommonJS
}
```

### pnpm workspace
```yaml
# pnpm-workspace.yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

```json
// apps/web/package.json 引用 packages/utils
{
  "dependencies": {
    "utils": "workspace:*"  // 始终指向本地 packages/utils
  }
}
```

### 路径别名（tsconfig.json）
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@utils/*": ["src/utils/*"]
    }
  }
}
```

## 练手项目（3小时）

### 项目：Week1 LLM Tool - 模块化整理

**需求**：

```json
// projects/week-01-llm-tool/package.json
{
  "name": "llm-tool",
  "version": "0.1.0",
  "type": "module",
  "exports": {
    ".": "./dist/index.js",
    "./types": "./dist/types.js",
    "./client": "./dist/client.js"
  },
  "types": "./dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "node --experimental-vm-modules node_modules/jest/bin/jest.js"
  }
}
```

```typescript
// src/index.ts - 统一导出
export * from './types.js';
export * from './guards.js';
export * from './config.js';
export * from './request.js';
export * from './client.js';

// src/client.ts - 使用路径别名
import { request } from '@/request';        // 而不是 ../../request
import type { LLMRequest } from '@/types';
```

```json
// tsconfig.json（项目内）
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"]
}
```

**Scaffolding**：
```
projects/week-01-llm-tool/
├── package.json       # 需要你创建
├── tsconfig.json     # 需要你创建
├── src/
│   ├── index.ts       # 统一导出（已有部分）
│   ├── client.ts      # 更新使用别名
│   └── ...
└── dist/              # 编译输出（.gitignore）
```

## 调试复盘（1小时）

### 验证方式
```bash
cd projects/week-01-llm-tool
pnpm install
pnpm build
node dist/client.js
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 配置 package.json（type: module, exports）
- [ ] 配置 tsconfig.json（outDir, paths 别名）
- [ ] 更新所有 import 使用别名
- [ ] 成功编译并运行
- [ ] 记录 package.json 和 tsconfig 配置要点
