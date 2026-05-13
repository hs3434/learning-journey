# Day 1：OpenCode 源码克隆与本地调试

## 今日目标
克隆 OpenCode 源码，运行本地开发服务器，理解项目结构

## 学习资料

### 英文（主要）
- [OpenCode GitHub](https://github.com/anomalyco/opencode)
- [OpenCode Contributing](https://github.com/anomalyco/opencode/blob/main/CONTRIBUTING.md)

### 中文（辅助）
- OpenCode README（克隆后查看）

## 理论学习（1小时）

### 克隆与安装
```bash
# 克隆到 opencode 目录
git clone https://github.com/anomalyco/opencode.git opencode
cd opencode

# 查看分支
git branch -a

# 查看最近的 tag（确定稳定版本）
git tag | tail -10

# 安装依赖（pnpm workspace）
pnpm install

# 构建
pnpm build

# 启动开发服务器
pnpm dev
```

### 项目结构
```
opencode/
├── apps/
│   └── desktop/           # Electron 桌面应用
├── packages/
│   ├── core/              # 核心逻辑
│   ├── adapters/          # 模型适配器
│   │   └── openai/        # OpenAI 兼容适配
│   └── ui/                # UI 组件
├── package.json           # Workspace 配置
└── pnpm-workspace.yaml    # pnpm workspace 定义
```

## 练手项目（1.5小时）

### 项目：Week4 OpenCode Debug - 环境搭建

**需求**：

```bash
# 1. 克隆 OpenCode（如果还没有）
# 已在 /work/run/projects/bio-24/learning-journey/opencode

# 2. 查看项目结构
ls -la opencode/
ls -la opencode/packages/
ls -la opencode/apps/

# 3. 查看 package.json 了解 scripts
cat opencode/package.json

# 4. 编译核心包
cd opencode/packages/core
pnpm build

# 5. 尝试启动
cd opencode
pnpm dev
```

**Scaffolding**：

```bash
# projects/week-04-opencode-debug/
# 克隆后在此记录调试步骤

# 工作目录：/work/run/projects/bio-24/learning-journey/opencode

# 记录你遇到的问题和解决方案
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd opencode
# 检查是否启动成功
curl http://localhost:3000 2>/dev/null && echo "Server running" || echo "Check logs"

# 查看日志
tail -f packages/*/dist/*.log 2>/dev/null || true
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 克隆 OpenCode 成功
- [ ] pnpm install 成功
- [ ] pnpm build 成功
- [ ] pnpm dev 启动成功
- [ ] 记录项目结构和关键入口
