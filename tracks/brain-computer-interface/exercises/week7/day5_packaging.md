# Week 7 Day 5: Packaging and Distribution

## 核心概念

### 1. pyproject.toml

```toml
[project]
name = "bci-toolkit"
version = "0.1.0"
description = "BCI signal processing toolkit"
requires-python = ">=3.11"
dependencies = [
    "numpy>=2.0",
    "scipy>=1.14",
    "mne>=1.7",
    "scikit-learn>=1.5",
    "pyqt6>=6.11.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "mypy>=2.1",
]

[project.scripts]
bci-gui = "bci.gui:main"
```

### 2. 目录结构

```
bci-toolkit/
├── pyproject.toml
├── src/
│   └── bci/
│       ├── __init__.py
│       ├── gui/
│       │   └── main.py
│       └── pipeline/
│           └── core.py
├── tests/
├── docs/
└── LICENSE
```

### 3. 安装模式

```bash
# 开发模式安装
pip install -e .

# 构建分发
pip install build
python -m build

# 安装 wheel
pip install dist/*.whl
```

### 4. 虚拟环境

```bash
# 使用 uv
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# 使用 conda
conda create -n bci python=3.11
conda activate bci
pip install -e .
```

### 5. 多平台打包

```python
# PyInstaller
pyinstaller --onefile --windowed bci/gui/main.py

# Nuitka
nuitka --standalone bci/gui/main.py
```

## 发布到 PyPI

```bash
# 注册 PyPI 账号

# 构建
python -m build

# 上传
twine upload dist/*
```

## 版本管理

```toml
[project]
version = "0.1.0"  # 语义版本

# 0.1.0 -> 0.2.0: 新功能
# 0.1.0 -> 1.0.0: Breaking changes
# 0.1.0 -> 0.1.1: Bug fixes
```

## 练习要点

1. 掌握 pyproject.toml
2. 学会打包分发
3. 理解版本管理

## 参考资料

- [Python 打包指南](https://packaging.python.org/)
- [uv 文档](https://docs.astral.sh/uv/)
- [PyInstaller](https://pyinstaller.org/)