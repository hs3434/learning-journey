# Learning Journey

个人多路线学习仓库，每条路线独立管理环境、笔记和项目代码。

## 项目结构

```
learning-journey/
├── README.md
├── AGENTS.md                              # AI 助手上下文
├── .gitignore
├── pyproject.toml                         # 根项目（空依赖）
├── notes/                                 # 通用笔记
├── tracks/
│   ├── brain-computer-interface/          # BCI 脑机接口路线
│   │   ├── pyproject.toml                 # BCI 路线依赖
│   │   ├── uv.lock                        # 依赖版本锁定
│   │   ├── plans/                         # 学习计划
│   │   ├── notes/                         # 学习笔记
│   │   └── projects/                      # 配套项目代码
│   │       ├── signal-processor/          # 信号处理器
│   │       ├── mne-pipeline/              # MNE 分析流水线
│   │       ├── eeg-viewer/                # EEG 查看器
│   │       ├── bci-decoder/               # BCI 解码器
│   │       ├── bci-gui/                   # BCI 图形界面
│   │       ├── bci-pipeline/              # BCI 工程化流水线
│   │       └── bci-data-utils/            # 数据工具
│   └── js-opencode/                       # JS/TS/Effect/OpenCode 路线
│       ├── plans/
│       └── projects/
```

## 路线概览

| 路线 | 描述 | 学习计划 | 语言 |
|------|------|----------|------|
| `brain-computer-interface/` | BCI 软件工程师 | [learning-plan-bci.md](tracks/brain-computer-interface/plans/learning-plan-bci.md) | Python |
| `js-opencode/` | JS/TS/Node/Effect/OpenCode | plans/ | JavaScript/TypeScript |

---

## 环境配置

### 前置要求

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) — Python 包管理器

安装 uv：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### BCI 路线

```bash
cd tracks/brain-computer-interface

# 1. 创建虚拟环境
uv venv

# 2. 安装依赖
#    方式 A：uv sync（推荐，网络通畅时）
uv sync

#    方式 B：pip（Docker 环境或 uv sync 异常时的替代方案）
.venv/bin/python -m ensurepip
.venv/bin/python -m pip install -r <(uv export -q --no-hashes | grep -v '^#')

# 3. 激活环境
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 4. 验证
python -c "import mne; print(f'MNE {mne.__version__}')"
```

**国内镜像**：`pyproject.toml` 已配置清华 tuna 镜像源，国内环境无需额外配置。如需使用官方源，删除 `[tool.uv]` 中的 `index-url` 即可。

**运行练习脚本**：

```bash
cd tracks/brain-computer-interface
source .venv/bin/activate
python projects/signal-processor/exercises/day7_preprocessing.py
```

### JS 路线

```bash
cd tracks/js-opencode
# 各项目独立安装
cd projects/week-00-js-reinforcement
npm install   # 或 pnpm install
```

---

## 依赖说明

### BCI 核心依赖

| 包 | 用途 |
|----|------|
| [numpy](https://numpy.org/) | 数值计算基础 |
| [scipy](https://scipy.org/) | 信号处理（滤波、频谱分析） |
| [matplotlib](https://matplotlib.org/) | 可视化绘图 |
| [mne](https://mne.tools/) | EEG/MEG 数据分析核心工具 |
| [scikit-learn](https://scikit-learn.org/) | 机器学习分类器 |
| [pooch](https://www.fatiando.org/pooch/) | MNE 示例数据下载 |

### 新增依赖

```bash
cd tracks/brain-computer-interface

# 添加依赖到 pyproject.toml
uv add <package-name>

# 如果 uv sync 不可用，手动安装：
.venv/bin/python -m pip install <package-name>
# 然后更新锁文件：
uv lock
```

---

## 常见问题

### Docker 容器环境

容器重置后需重新创建虚拟环境：

```bash
cd /workspace/learning-journey/tracks/brain-computer-interface
uv venv
.venv/bin/python -m ensurepip
.venv/bin/python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    numpy scipy matplotlib mne scikit-learn pooch
```

### `uv sync` 报 rayon 线程池错误

Docker 容器内可能遇到 `ThreadPoolBuildError`，这是 uv 的并发限制问题。使用上面的 pip 替代方案即可。

### MNE 示例数据

首次运行练习脚本会自动下载 MNE 示例数据（~30MB），需要网络连接。数据缓存到 `~/mne_data/`。
