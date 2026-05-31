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

## 测试数据

```bash
# 设置数据目录（按需修改）
export BCI_DATA=/path/to/bci_data
mkdir -p $BCI_DATA

# 下载运动想象数据 (PhysioNet EEGBCI)
uv run python -c "
import mne, shutil, os
files = mne.datasets.eegbci.load_data(1, [4, 6, 8, 10], path='$BCI_DATA', update_path=False)
for f in files:
    shutil.copy(f, os.path.join('$BCI_DATA', os.path.basename(f)))
"

# 下载听觉/视觉 ERP 数据 (MNE Sample, ~1.6GB)
uv run python -c "
import mne
mne.datasets.sample.data_path(path='$BCI_DATA', update_path=False)
"
```

数据下载后目录结构：
```
$BCI_DATA/
├── S001R04.edf ~ S001R10.edf      运动想象 (160Hz, 64ch)
└── MNE-sample-data/                听觉/视觉 ERP (600Hz, 306ch MEG+EOG+STIM)
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
uv run bci $BCI_DATA/S001R04.edf --method mi
uv run bci $BCI_DATA/MNE-sample-data/MEG/sample/sample_audvis_raw.fif --method lda

# GUI 模式 (需要 X11 转发)
export DISPLAY=localhost:10.0
uv run bci
```

## 测试

```bash
# 安装测试依赖
uv sync --group dev

# 运行所有测试
uv run pytest

# 运行指定模块测试
uv run pytest bci/tests/test_decoder.py

# 多进程加速（需先安装 pytest-xdist）
uv add --group dev pytest-xdist
uv run pytest -n auto
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
