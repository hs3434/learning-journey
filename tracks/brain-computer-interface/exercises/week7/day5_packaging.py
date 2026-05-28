"""
Week 7 Day 5: Packaging and Distribution
========================================
打包、分发、虚拟环境
将项目打包为可安装工具
"""
import subprocess
import sys
from pathlib import Path

# ============================================================
# 1. pyproject.toml 结构
# ============================================================
print("=" * 60)
print("1. pyproject.toml 结构")
print("=" * 60)

pyproject_content = """
[project]
name = "bci-toolkit"
version = "0.1.0"
description = "BCI signal processing toolkit"
requires-python = ">=3.11"
dependencies = [
    "numpy>=2.0",
    "scipy>=1.14",
    "matplotlib>=3.9",
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
bci-pipeline = "bci.pipeline:main"

[build-system]
requires = "setuptools>=61.0"
build-backend = "setuptools.build_meta"
"""

print(pyproject_content)

# ============================================================
# 2. 目录结构
# ============================================================
print("\n" + "=" * 60)
print("2. 目录结构")
print("=" * 60)

structure = """
bci-toolkit/
├── pyproject.toml
├── src/
│   └── bci/
│       ├── __init__.py
│       ├── gui/
│       │   ├── __init__.py
│       │   └── main.py
│       ├── pipeline/
│       │   ├── __init__.py
│       │   └── main.py
│       └── utils/
│           ├── __init__.py
│           └── signal.py
├── tests/
│   ├── __init__.py
│   ├── test_signal.py
│   └── test_pipeline.py
├── docs/
│   └── README.md
└── LICENSE
"""
print(structure)

# ============================================================
# 3. setup.cfg 配置
# ============================================================
print("\n" + "=" * 60)
print("3. setup.cfg 配置")
print("=" * 60)

setup_cfg = """
[metadata]
name = bci-toolkit
version = 0.1.0
description = BCI signal processing toolkit
long_description = file: README.md
long_description_content_type = text/markdown
license = MIT
classifiers =
    Development Status :: 3 - Alpha
    Intended Audience :: Science/Research
    Programming Language :: Python :: 3.11

[options]
packages = find:
python_requires = >=3.11
install_requires =
    numpy>=2.0
    scipy>=1.14
    mne>=1.7

[options.packages.find]
where = src

[options.entry_points]
console_scripts =
    bci-gui = bci.gui:main
"""
print(setup_cfg)

# ============================================================
# 4. 虚拟环境操作
# ============================================================
print("\n" + "=" * 60)
print("4. 虚拟环境操作")
print("=" * 60)

venv_path = Path("/tmp/bci-test-venv")
print(f"虚拟环境路径: {venv_path}")

commands = [
    "创建虚拟环境: uv venv /tmp/bci-test-venv",
    "激活环境: source /tmp/bci-test-venv/bin/activate",
    "安装包: uv pip install numpy scipy mne",
    "安装开发模式: uv pip install -e .",
    "查看已安装: uv pip list",
]

for cmd in commands:
    print(f"  {cmd}")

# ============================================================
# 5. build 和分发
# ============================================================
print("\n" + "=" * 60)
print("5. build 和分发")
print("=" * 60)

dist_commands = [
    "构建源码分发: python -m build --sdist",
    "构建 wheel: python -m build --wheel",
    "上传到 PyPI: twine upload dist/*",
    "安装本地 wheel: pip install dist/*.whl",
]

for cmd in dist_commands:
    print(f"  {cmd}")

# ============================================================
# 6. 多平台打包
# ============================================================
print("\n" + "=" * 60)
print("6. 多平台打包")
print("=" * 60)

cross_platform = """
# PyInstaller 单文件打包
pyinstaller --onefile --windowed bci/gui/main.py

# Nuitka 编译
nuitka --standalone --windows-disable-console bci/gui/main.py

# py2app (macOS)
python setup.py py2app

# py2exe (Windows)
python setup.py py2exe
"""
print(cross_platform)

print("\n✅ Day 5 完成!")