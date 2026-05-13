# Day 4：CLI 参数解析、交互式输入

## 今日目标
实现命令行参数解析（commander/yargs）、交互式输入获取

## 学习资料

### 英文（主要）
- [commander.js](https://github.com/tj/commander.js)
- [inquirer.js](https://github.com/SBoudrias/Inquirer.js)

### 中文（辅助）
- [commander.js 中文文档](https://juejin.cn/post/6844903861254307848)

## 理论学习（1小时）

### commander.js 基础
```javascript
import { Command } from 'commander';

const program = new Command();

program
  .name('my-cli')
  .description('CLI tool description')
  .version('1.0.0');

program
  .command('init')
  .description('Initialize project')
  .option('-n, --name <name>', 'project name')
  .option('-t, --template <template>', 'template name', 'default')
  .action((options) => {
    console.log('Init with:', options);
  });

program
  .command('build <source>')
  .description('Build project')
  .option('-o, --output <dir>', 'output directory', './dist')
  .option('--watch', 'watch mode')
  .action((source, options) => {
    console.log(`Building ${source} to ${options.output}`);
  });

program.parse();
```

### 交互式输入 inquirer
```javascript
import inquirer from 'inquirer';

const answers = await inquirer.prompt([
  {
    type: 'input',
    name: 'projectName',
    message: 'Project name:',
    default: 'my-project'
  },
  {
    type: 'list',
    name: 'template',
    message: 'Select template:',
    choices: ['typescript', 'javascript', 'rust']
  },
  {
    type: 'confirm',
    name: 'install',
    message: 'Install dependencies?',
    default: true
  }
]);

console.log(answers);
```

### 组合使用
```javascript
// 自定义 help 输出
program
  .command('deploy')
  .description('Deploy to server')
  .option('-e, --env <env>', 'environment', 'production')
  .addHelpText('after', '\nExamples:\n  my-cli deploy -e staging')
  .action(options => deploy(options));
```

## 练手项目（1.5小时）

### 项目：Week2 CLI Tool - 命令注册与参数解析

**需求**：

```javascript
// src/cli/program.js
import { Command } from 'commander';
import { createLogger } from '../utils/logger.js';

const logger = createLogger();

export function createProgram() {
  const program = new Command();

  program
    .name('learn-cli')
    .description('Learning project CLI tool')
    .version('0.1.0');

  // init 命令
  program
    .command('init')
    .description('Initialize a new project')
    .option('-n, --name <name>', 'project name', 'untitled')
    .option('-t, --template <template>', 'template', 'default')
    .action((options) => {
      logger.info('Initializing project:', options.name);
      logger.debug('Template:', options.template);
    });

  // config 命令
  program
    .command('config')
    .description('Manage configuration')
    .option('-s, --show', 'show current config')
    .option('-r, --reset', 'reset to defaults')
    .action((options) => {
      if (options.show) logger.info('Showing config...');
      if (options.reset) logger.info('Resetting config...');
    });

  return program;
}
```

**Scaffolding**：

```javascript
// projects/week-02-cli-tool/src/cli/program.js
import { Command } from 'commander';
import { createLogger } from '../utils/logger.js';

const logger = createLogger();

export function createProgram() {
  const program = new Command();
  // TODO: 配置 program（name, description, version）

  // TODO: 添加 init 命令

  // TODO: 添加 config 命令

  return program;
}

// projects/week-02-cli-tool/src/index.js
import { createProgram } from './cli/program.js';

const program = createProgram();
program.parse();
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-02-cli-tool
node src/index.js --help
node src/index.js init --name myapp --template ts
node src/index.js config --show
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现 createProgram 函数
- [ ] 添加 init 命令（含选项）
- [ ] 添加 config 命令（含选项）
- [ ] 正确解析参数
- [ ] 无运行时错误
