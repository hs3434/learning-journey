# AGENTS.md

## 仓库用途

个人学习计划仓库，支持多条独立的学习路线（track）。

## 项目结构

```
/learning-journey
├── tracks/                         # 学习路线目录
│   ├── js-opencode/                # JS/TS/Effect/OpenCode 学习路线
│   │   ├── plans/                  # 学习计划文档
│   │   └── projects/               # 配套小项目代码
│   └── brain-computer-interface/   # 脑机接口学习路线
│       ├── plans/                  # 学习计划
│       ├── notes/                  # 路线笔记（岗位 JD、简历、面试准备等）
│       ├── exercises/              # 每周练习脚本
│       └── package/                # 主项目 bci 包
├── notes/                          # 通用笔记、复盘记录（与具体路线无关）
└── AGENTS.md                      # 本文件
```

## 路线索引

| 路线 | 描述 | 入口计划 |
|------|------|----------|
| `tracks/js-opencode/` | JS/TS/Node/Effect/OpenCode 学习 | `plans/learning-plan-v2.md` |
| `tracks/brain-computer-interface/` | BCI 软件工程师（Python/Qt/信号处理） | `plans/learning-plan-bci.md` |

## 开发环境

每条路线独立管理环境，互不干扰。

**brain-computer-interface 路线**：
- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) 包管理器
- 虚拟环境：`tracks/brain-computer-interface/package/.venv/`
- 依赖声明：`tracks/brain-computer-interface/package/pyproject.toml`
- 国内镜像已配置（清华 tuna，`~/.config/uv/uv.toml`）
- CNN 解码器需要 PyTorch（可选）：
  ```bash
  uv pip install torch --index-url https://download.pytorch.org/whl/cpu
  ```

**js-opencode 路线**：
- Node.js 18+
- pnpm（OpenCode monorepo 使用 pnpm workspace）
- TypeScript 5.x

## 常用命令

```bash
# 查看所有路线
ls tracks/

# BCI 路线
cd tracks/brain-computer-interface/package
uv sync                                 # 安装基础依赖
uv pip install torch --index-url https://download.pytorch.org/whl/cpu  # CNN 可选
uv run bci --gui                        # 启动 GUI

# JS 路线
cd tracks/js-opencode/projects/week-00-js-reinforcement
npm install && npm run dev
```

## 复盘格式（每周结束填写）

```markdown
## WeekX 复盘
### 完成 vs 计划
-
### 核心问题
-
### 下周调整
-
```