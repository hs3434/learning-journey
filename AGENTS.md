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
│       ├── plans/                  # 学习计划文档
│       └── projects/               # 配套小项目代码
├── notes/                          # 通用笔记、复盘记录
└── AGENTS.md                      # 本文件
```

## 路线索引

| 路线 | 描述 | 入口计划 |
|------|------|----------|
| `tracks/js-opencode/` | JS/TS/Node/Effect/OpenCode 学习 | `plans/learning-plan-v2.md` |
| `tracks/brain-computer-interface/` | BCI 软件工程师（Python/Qt/信号处理） | `plans/learning-plan-bci.md` |

## 开发环境

根据学习路线而定。

**js-opencode 路线**：
- Node.js 18+
- pnpm（OpenCode monorepo 使用 pnpm workspace）
- TypeScript 5.x

**brain-computer-interface 路线**：
- Python 3.9+
- conda 或 venv 虚拟环境
- PyQt6 / PySide6（GUI）
- mne, numpy, scipy, scikit-learn

## 通用命令

```bash
# 查看所有路线
ls tracks/

# 进入某路线
cd tracks/js-opencode/
cd tracks/brain-computer-interface/

# BCI 路线环境配置示例
conda create -n bci python=3.10
conda activate bci
pip install mne numpy scipy pyqt6 scikit-learn
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