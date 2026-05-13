# Day 2：child_process / execa、子进程通信

## 今日目标
掌握 Node.js 子进程创建、命令执行、进程间通信

## 学习资料

### 英文（主要）
- [Node.js child_process](https://nodejs.org/api/child_process.html)
- [execa 文档](https://github.com/sindresorhus/execa)

### 中文（辅助）
- [Node.js 子进程详解](https://juejin.cn/post/6844903952875945998)

## 理论学习（1小时）

### child_process 基础
```javascript
import { spawn, exec, execSync } from 'child_process';

// spawn：流式输出，适合长时间命令
const child = spawn('npm', ['install'], {
  cwd: './project',
  stdio: 'inherit'
});

child.on('exit', (code) => {
  console.log(` exited with code ${code}`);
});

// exec：一次性输出，适合短命令
exec('git status', (error, stdout, stderr) => {
  if (error) console.error(error);
  console.log(stdout);
});

// execSync：同步版本（阻塞）
const output = execSync('ls -la', { encoding: 'utf-8' });
```

### execa（更现代的封装）
```javascript
import { execa } from 'execa';

// 基本用法
const { stdout } = await execa('git', ['status']);

// 管道输出
await execa('git', ['log', '--oneline']).pipeStdout(process.stdout);

// 捕获输出
const { stdout, stderr } = await execa('npm', ['run', 'build']);

// 超时
await execa('sleep', ['10'], { timeout: 1000 });
```

### 进程通信
```javascript
// 父进程
const child = spawn('node', ['child.js'], { stdio: ['pipe', 'pipe', 'pipe', 'ipc'] });

child.on('message', (msg) => {
  console.log('来自子进程:', msg);
});

child.send({ type: 'init' });

// 子进程（child.js）
process.on('message', (msg) => {
  console.log('来自父进程:', msg);
  process.send({ type: 'ready' });
});
```

## 练手项目（1.5小时）

### 项目：Week2 CLI Tool - 命令执行模块

**需求**：

```javascript
// src/command/runner.js
import { execa } from 'execa';

export async function runCommand(cmd, args = [], options = {}) {
  const { stdout, stderr, exitCode } = await execa(cmd, args, {
    stdio: 'pipe',
    ...options
  });
  return { stdout, stderr, exitCode, success: exitCode === 0 };
}

export async function runCommandLive(cmd, args = []) {
  return await execa(cmd, args, {
    stdout: 'inherit',
    stderr: 'inherit'
  });
}

export async function runCommandWithTimeout(cmd, args = [], timeoutMs = 30000) {
  try {
    return await execa(cmd, args, { timeout: timeoutMs });
  } catch (error) {
    if (error.isTerminated) {
      return { stdout: '', stderr: 'TIMEOUT', exitCode: 124, success: false };
    }
    throw error;
  }
}
```

**Scaffolding**：

```javascript
// projects/week-02-cli-tool/src/command/runner.js
import { execa } from 'execa';

export async function runCommand(cmd, args = [], options = {}) {
  // TODO: 实现
}

export async function runCommandLive(cmd, args = []) {
  // TODO: 实现（直接输出到终端）
}

export async function runCommandWithTimeout(cmd, args = [], timeoutMs = 30000) {
  // TODO: 实现（超时处理）
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-02-cli-tool
node src/command/runner.js
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现 runCommand 函数
- [ ] 实现 runCommandLive 函数
- [ ] 实现 runCommandWithTimeout 函数（含超时处理）
- [ ] 无运行时错误
