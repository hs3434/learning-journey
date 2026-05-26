# Week 7 Day 25：打包分发与项目工程化

## 1. 为什么需要打包？

```
没有打包：
  同事: "你那个 BCI 工具怎么用？"
  你: "你把这三个文件夹拷过去，装 numpy scipy mne matplotlib sklearn..."
  同事: "装了半天，import 报错了"
  你: "你 Python 版本多少？3.10 以上的话有个兼容问题..."

打包后：
  同事: "你那个 BCI 工具怎么用？"
  你: "pip install bci-pipeline"
  同事: "完了，能用了"
```

### 打个比方

- 没有打包 = 给别人一堆零件 + 组装说明书
- 打包后 = 给别人一台装好的笔记本电脑

---

## 2. pyproject.toml（现代 Python 打包）

### 2.1 基本配置

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "bci-pipeline"
version = "0.1.0"
description = "A modular BCI data analysis pipeline"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"

authors = [
    {name = "Your Name", email = "your@email.com"},
]

dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "matplotlib>=3.7",
    "mne>=1.4",
    "scikit-learn>=1.2",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "mypy>=1.0",
    "sphinx>=6.0",
    "sphinx-rtd-theme>=1.2",
]
gui = [
    "PyQt6>=6.5",
]

[project.scripts]
bci-run = "bci.cli:main"

[project.entry-points."bci.loaders"]
mne = "bci.loaders:MNEDataLoader"
eeglab = "bci.loaders:EEGLABLoader"
```

### 2.2 包结构

```
bci-pipeline/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── bci/
│       ├── __init__.py
│       ├── config.py
│       ├── loader.py
│       ├── preprocessor.py
│       ├── epocher.py
│       ├── decoder.py
│       ├── exporter.py
│       ├── pipeline.py
│       └── cli.py
├── tests/
│   ├── conftest.py
│   ├── test_preprocessor.py
│   ├── test_epocher.py
│   └── test_decoder.py
└── docs/
    ├── conf.py
    ├── index.rst
    └── Makefile
```

---

## 3. CLI 工具

### 3.1 argparse 基础

```python
# bci/cli.py
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        prog='bci-run',
        description='BCI Data Analysis Pipeline'
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # run 子命令
    run_parser = subparsers.add_parser('run', help='Run full pipeline')
    run_parser.add_argument('data_path', help='Path to EEG data file')
    run_parser.add_argument('-c', '--config', default='bci_config.yaml',
                           help='Path to config YAML')
    run_parser.add_argument('-o', '--output', default='./output',
                           help='Output directory')
    run_parser.add_argument('-v', '--verbose', action='store_true')
    
    # validate 子命令
    val_parser = subparsers.add_parser('validate', help='Validate config')
    val_parser.add_argument('config_path', help='Path to config YAML')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        from bci.pipeline import BCIPipeline
        from bci.config import ConfigManager
        
        config = ConfigManager.from_yaml(args.config)
        pipeline = BCIPipeline(config)
        result = pipeline.run(args.data_path)
        print(f"Accuracy: {result.scores['accuracy']:.1%}")
    
    elif args.command == 'validate':
        from bci.config import ConfigManager
        config = ConfigManager.from_yaml(args.config_path)
        errors = ConfigManager.validate(config)
        if errors:
            for e in errors:
                print(f"ERROR: {e}")
            sys.exit(1)
        else:
            print("Config is valid!")

if __name__ == '__main__':
    main()
```

### 3.2 使用方式

```bash
# 安装后
pip install -e .

# 运行 Pipeline
bci-run run eeg_raw.fif -c config.yaml -o ./results

# 验证配置
bci-run validate config.yaml

# 帮助
bci-run --help
bci-run run --help
```

---

## 4. CI/CD（持续集成）

### 4.1 GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=bci --cov-report=xml
      
      - name: Type check
        run: |
          mypy src/bci/ --ignore-missing-imports
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 5. 版本管理

### 5.1 语义化版本 (SemVer)

```
v MAJOR.MINOR.PATCH
  │     │     │
  │     │     └── Bug 修复（向后兼容）
  │     └──────── 新功能（向后兼容）
  └────────────── 破坏性变更（不兼容）

示例：
0.1.0 → 首个可用版本
0.1.1 → 修复了滤波参数校验的 bug
0.2.0 → 新增 SSVEP 解码支持
1.0.0 → API 稳定，正式发布
```

### 5.2 CHANGELOG

```markdown
# Changelog

## [0.2.0] - 2026-05-26

### Added
- SSVEP decoder with CCA/FBCCA
- Real-time visualization mode
- HDF5 export support

### Changed
- FilterConfig now validates on creation
- Epoch extraction is 2x faster with vectorized baseline

### Fixed
- Bandpass filter edge case when l_freq = 0
- PSD plot colorbar range issue
```

---

## 6. 项目工程化清单

```
✅ pyproject.toml         — 包配置 + 依赖声明
✅ src/ layout            — 源码与测试分离
✅ CLI 工具               — bci-run 命令行入口
✅ 测试套件               — pytest + 覆盖率
✅ 类型检查               — mypy
✅ 文档                   — Sphinx + autodoc
✅ CI/CD                  — GitHub Actions
✅ 语义化版本             — SemVer
✅ CHANGELOG              — 变更记录
✅ README                 — 项目入口文档
✅ LICENSE                — 开源协议
✅ .gitignore             — 忽略规则
```

---

## 7. Week 7 总结 + 整体回顾

### Week 7 收获

| Day | 主题 | 核心技能 |
|-----|------|----------|
| 21 | 模块化 + 配置 | SRP、依赖注入、dataclass、YAML |
| 22 | 日志 + 异常 | logging、自定义异常、优雅降级 |
| 23 | 测试 | pytest、参数化、Mock、覆盖率 |
| 24 | 文档 + 类型 | type hints、docstring、Sphinx |
| 25 | 打包 + 工程化 | pyproject.toml、CLI、CI/CD、SemVer |

### 8 周学习路线回顾

```
Week 1-2: Python 科学计算 + Qt GUI 基础      ✅
Week 3-4: 信号处理 + MNE-Python               ✅
Week 5-6: BCI 解码 + GUI 整合                  ✅
Week 7:   Pipeline 工程化                      ✅ ← 今天完成
Week 8:   项目整合 + 面试准备                   🔜
```

从一个零 BCI 经验的生物信息工程师，到现在能：
- 用 MNE 处理 EEG 数据
- 实现 SSVEP/MI/P300 解码
- 构建 Qt GUI 分析工具
- 工程化地打包、测试、文档化一个 BCI 项目

下一步 Week 8：**项目整合 + 面试准备** — 把 8 周积累整合为可展示的完整项目！
