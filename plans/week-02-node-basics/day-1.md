# Day 1：Node.js 模块系统、fs 文件读写

## 今日目标
掌握 Node.js 原生 fs 模块的文件读写、环境变量加载、路径处理

## 学习资料

### 英文（主要）
- [Node.js fs module](https://nodejs.org/api/fs.html)
- [Node.js path module](https://nodejs.org/api/path.html)
- [Node.js process](https://nodejs.org/api/process.html)

### 中文（辅助）
- [Node.js 文件系统模块](https://nodejs.net.cn/api/fs.html)

## 理论学习（1小时）

### 文件读写
```javascript
import { readFile, writeFile, readFileSync, writeFileSync } from 'fs/promises';
import { existsSync, mkdirSync } from 'fs';

// 异步（推荐）
const content = await readFile('./data.json', 'utf-8');
await writeFile('./output.json', JSON.stringify(data), 'utf-8');

// 同步（仅启动脚本用）
const config = JSON.parse(readFileSync('./config.json', 'utf-8'));

// 检查+创建
if (!existsSync('./data')) mkdirSync('./data', { recursive: true });
```

### 环境变量
```javascript
// .env 文件用 dotenv 加载
import 'dotenv/config';

// 访问
const port = process.env.PORT ?? 3000;
const apiKey = process.env.API_KEY;
```

### 路径处理
```javascript
import { join, resolve, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const __dirname = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

// 路径拼接
const configPath = resolve(__dirname, '../config/settings.json');
```

## 练手项目（1.5小时）

### 项目：Week2 CLI Tool - 配置读写模块

**目标**：实现配置文件读写，作为 CLI 工具的基础

**需求**：

```javascript
// src/config/index.js
import { readFile, writeFile } from 'fs/promises';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync, mkdirSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

export async function loadConfig(name = 'config') {
  const configDir = resolve(__dirname, '../../config');
  const configPath = resolve(configDir, `${name}.json`);

  if (!existsSync(configPath)) {
    return null;
  }

  const content = await readFile(configPath, 'utf-8');
  return JSON.parse(content);
}

export async function saveConfig(name, data) {
  const configDir = resolve(__dirname, '../../config');
  if (!existsSync(configDir)) {
    mkdirSync(configDir, { recursive: true });
  }

  const configPath = resolve(configDir, `${name}.json`);
  await writeFile(configPath, JSON.stringify(data, null, 2), 'utf-8');
}

export function getConfigPath(name = 'config') {
  const configDir = resolve(__dirname, '../../config');
  return resolve(configDir, `${name}.json`);
}
```

**Scaffolding**：

```javascript
// projects/week-02-cli-tool/src/config/index.js
// 配置文件读写模块

export async function loadConfig(name = 'config') {
  // TODO: 实现
}

export async function saveConfig(name, data) {
  // TODO: 实现
}

export function getConfigPath(name = 'config') {
  // TODO: 实现
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-02-cli-tool
node --experimental-vm-modules src/config/index.js
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现 loadConfig 函数
- [ ] 实现 saveConfig 函数（自动创建目录）
- [ ] 实现 getConfigPath 函数
- [ ] 无运行时错误
