# BCI Signal Processing Pipeline

```
bci/
├── config/       配置管理 (YAML/dataclass)
├── loader/       EEG 数据加载 (EDF/FIF/EEGLAB/BrainVision)
├── preprocessor/ 信号预处理 (滤波/ICA/参考)
├── epocher/      事件检测与分段
├── decoder/      解码器 (LDA/MI/SSVEP)
├── pipeline/     流水线编排
├── gui/          Qt GUI (PyQt6)
├── tests/        单元测试
└── main.py       入口
```

## 环境配置

```bash
# 用户本地库路径（GUI 依赖 libxcb-cursor）
export LD_LIBRARY_PATH=$HOME/../../.local/lib:$LD_LIBRARY_PATH

# 追加到 ~/.bashrc 持久化
echo 'export LD_LIBRARY_PATH=$HOME/../../.local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
```

## 快速开始

```bash
cd projects

# 首次安装
uv sync

# CLI 模式
uv run bci data.edf --method lda
uv run bci data.edf --method mi
uv run bci data.edf --method ssvep

# GUI 模式 (需要 X11 转发)
export DISPLAY=localhost:10.0
uv run bci
```

## 开发

```bash
# 类型检查
uv run mypy --namespace-packages --explicit-package-bases bci

# 静态分析
uv run pyright bci

# 交互调试
uv run ipython
>>> from bci.config import create_default_config
>>> from bci.pipeline import run_pipeline
>>> config = create_default_config()
>>> result = run_pipeline(config, "data.edf")

# 添加依赖
uv add <package>
```
