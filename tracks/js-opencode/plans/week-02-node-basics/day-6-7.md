# Day 6-7：Week2 项目整合与命令行工具架构

## 周末目标
整合 Week2 所学，实现完整的 CLI 工具骨架，理解 OpenCode 命令架构

## 学习资料

### 英文（主要）
- [OpenCode CLI 架构](https://github.com/anomalyco/opencode)
- [commander.js 最佳实践](https://github.com/tj/commander.js/blob/main/docs/patterns-of-programs.md)

## 项目整合（3小时）

### 项目：Week2 CLI Tool - 完整整合

**目标**：整合所有模块，形成可运行的 CLI 工具

**目录结构**：
```
projects/week-02-cli-tool/
├── src/
│   ├── index.js              # 入口
│   ├── cli/
│   │   └── program.js        # 命令注册
│   ├── config/
│   │   └── index.js          # 配置读写
│   ├── command/
│   │   └── runner.js         # 命令执行
│   ├── utils/
│   │   ├── logger.js         # 日志
│   │   └── env.js            # 环境变量
│   └── effect-llm.ts         # Effect 重构（可选）
├── config/                   # 配置文件目录
├── package.json
└── tsconfig.json
```

**package.json**：
```json
{
  "name": "week-02-cli-tool",
  "type": "module",
  "version": "0.1.0",
  "bin": {
    "learn-cli": "./src/index.js"
  },
  "scripts": {
    "start": "node src/index.js",
    "test": "echo \"No tests\""
  },
  "dependencies": {
    "commander": "^11.0.0",
    "execa": "^8.0.0"
  }
}
```

**入口文件**：
```javascript
// src/index.js
#!/usr/bin/env node
import { createProgram } from './cli/program.js';
import { loadConfig } from './config/index.js';

async function main() {
  const config = await loadConfig('cli');
  const program = createProgram(config);
  program.parse();
}

main().catch(console.error);
```

## OpenCode 命令架构分析（1小时）

### OpenCode CLI 结构参考
```javascript
// OpenCode 命令注册模式（简化）
class CommandRegistry {
  commands = new Map();

  register(name, command) {
    this.commands.set(name, command);
  }

  async execute(name, args) {
    const command = this.commands.get(name);
    if (!command) throw new Error(`Unknown command: ${name}`);
    return command.execute(args);
  }
}

// 全局单例
export const globalCommands = new CommandRegistry();

// 注册内置命令
globalCommands.register('init', new InitCommand());
globalCommands.register('config', new ConfigCommand());
globalCommands.register('run', new RunCommand());
```

### CLI 工具常用模式
```javascript
// 1. 全局命令 + 子命令
// cli.js init --template ts
// cli.js config set key value
// cli.js config get key

// 2. 交互式 prompt（可选参数时）
const { action } = await inquirer.prompt([
  { type: 'list', name: 'action', message: 'What to do?', choices: ['init', 'build', 'deploy'] }
]);

// 3. 配置文件优先级
// 1) 命令行参数
// 2) 环境变量
// 3) 本地 .clirc / .clirc.json
// 4) 全局 ~/.clirc
```

## 调试复盘（1小时）

### 验证方式
```bash
cd projects/week-02-cli-tool
# 安装依赖
npm install

# 测试命令
node src/index.js --help
node src/index.js init --name test --template ts
node src/index.js config --show

# 链接到全局（可选）
npm link
learn-cli --help
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] CLI 工具可正常运行
- [ ] init / config 命令可用
- [ ] 日志系统正常输出
- [ ] 配置文件可读写
- [ ] 理解 OpenCode 命令架构模式
