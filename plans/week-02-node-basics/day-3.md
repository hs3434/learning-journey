# Day 3：日志系统、环境变量、跨平台兼容

## 今日目标
实现分级日志系统、环境变量管理、跨平台路径处理

## 学习资料

### 英文（主要）
- [Node.js console](https://nodejs.org/api/console.html)
- [signale 日志库](https://github.com/klauscfhq/signale)

### 中文（辅助）
- [Node.js 日志最佳实践](https://juejin.cn/post/6844903601469333511)

## 理论学习（1小时）

### 日志分级
```javascript
const LOG_LEVELS = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3,
  trace: 4
};

const currentLevel = process.env.LOG_LEVEL || 'info';

function log(level, ...args) {
  if (LOG_LEVELS[level] <= LOG_LEVELS[currentLevel]) {
    const timestamp = new Date().toISOString();
    console[level === 'error' ? 'error' : 'log'](`[${timestamp}] [${level.toUpperCase()}]`, ...args);
  }
}

log.info('Starting server');
log.debug('Config loaded:', config);
log.error('Failed to connect', error);
```

### 环境变量类型转换
```javascript
// .env 文件
// PORT=3000
// DEBUG=true
// TIMEOUT=5000

// 读取时转换类型
const config = {
  port: parseInt(process.env.PORT, 10) || 3000,
  debug: process.env.DEBUG === 'true',
  timeout: parseInt(process.env.TIMEOUT, 10) || 30000
};
```

### 跨平台兼容
```javascript
import { platform } from 'os';

const isWindows = platform() === 'win32';

// Windows 下用 && 连接命令，Unix 下用 ;
const sep = isWindows ? ';' : ':';

// npm scripts 跨平台用 cross-env
// "build": "cross-env NODE_ENV=production webpack"
```

## 练手项目（1.5小时）

### 项目：Week2 CLI Tool - 日志与配置模块

**需求**：

```javascript
// src/utils/logger.js
const levels = { error: 0, warn: 1, info: 2, debug: 3, trace: 4 };

class Logger {
  constructor(level = 'info') {
    this.level = level;
  }

  _log(level, ...args) {
    if (levels[level] <= levels[this.level]) {
      const time = new Date().toISOString();
      console.log(`[${time}] [${level.toUpperCase().padEnd(5)}]`, ...args);
    }
  }

  error(...args) { this._log('error', ...args); }
  warn(...args) { this._log('warn', ...args); }
  info(...args) { this._log('info', ...args); }
  debug(...args) { this._log('debug', ...args); }
  trace(...args) { this._log('trace', ...args); }
}

export function createLogger(level = process.env.LOG_LEVEL || 'info') {
  return new Logger(level);
}

// src/utils/env.js
export function loadEnv() {
  const result = {};

  for (const [key, value] of Object.entries(process.env)) {
    if (key.startsWith('APP_')) {
      result[key] = value;
    }
  }

  return result;
}

export function getEnv(key, defaultValue, parseAs) {
  const value = process.env[key] ?? defaultValue;

  if (parseAs === 'number') return parseInt(value, 10);
  if (parseAs === 'boolean') return value === 'true' || value === '1';
  return value;
}
```

**Scaffolding**：

```javascript
// projects/week-02-cli-tool/src/utils/logger.js
// 分级日志模块

const levels = { /* TODO */ };

class Logger {
  // TODO
}

export function createLogger(level) {
  // TODO
}

// projects/week-02-cli-tool/src/utils/env.js
// 环境变量工具

export function loadEnv() {
  // TODO: 加载 APP_ 前缀的环境变量
}

export function getEnv(key, defaultValue, parseAs) {
  // TODO: 类型转换支持
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-02-cli-tool
LOG_LEVEL=debug node -e "import('./src/utils/logger.js').then(m => m.createLogger('debug').debug('test'))"
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现分级 Logger 类
- [ ] 实现 createLogger 工厂函数
- [ ] 实现 loadEnv 函数
- [ ] 实现 getEnv 函数（支持类型转换）
- [ ] 无运行时错误
