# Week 7 Day 1: Modular Design and Configuration

## 核心概念

### 1. 模块化设计原则

```
高内聚 + 低耦合
```

- 每个模块职责单一
- 模块间通过接口通信
- 避免直接依赖

### 2. Python 包结构

```
bci/
├── __init__.py
├── loader/
│   ├── __init__.py
│   └── data_loader.py
├── preprocessor/
│   ├── __init__.py
│   └── filters.py
├── pipeline/
│   ├── __init__.py
│   └── core.py
└── config/
    ├── __init__.py
    └── settings.py
```

### 3. Dataclass 配置

```python
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class FilterConfig:
    lowcut: float = 0.5
    highcut: float = 40.0
    notch_freq: Optional[int] = 50
    order: int = 4

@dataclass
class PipelineConfig:
    filter_params: FilterConfig = field(default_factory=FilterConfig)
    epoch_tmin: float = -0.2
    epoch_tmax: float = 0.5
    baseline: Tuple[Optional[float], Optional[float]] = (None, 0)
    channels: Optional[List[str]] = None
```

### 4. 单一职责原则

```python
# 好的设计
class DataLoader:
    def load(self, filepath: str) -> Raw:
        pass

class Preprocessor:
    def filter(self, raw: Raw, params: FilterConfig) -> Raw:
        pass

class EpochExtractor:
    def create_epochs(self, raw: Raw, events, params) -> Epochs:
        pass

# 避免：一个大类做所有事情
class BigClass:
    def load(self): pass
    def filter(self): pass
    def epoch(self): pass
    def decode(self): pass
```

## 配置管理

### YAML 配置

```yaml
# config.yaml
filter:
  lowcut: 0.5
  highcut: 40.0
  notch_freq: 50

epoch:
  tmin: -0.2
  tmax: 0.5
  baseline: [null, 0]

classifier:
  type: LDA
  n_components: 4
```

```python
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)
```

## 练习要点

1. 掌握模块化设计原则
2. 学会使用 dataclass
3. 理解配置管理

## 参考资料

- [Python dataclass](https://docs.python.org/3/library/dataclasses.html)
- [YAML 文档](https://pyyaml.org/wiki/PyYAMLDocumentation)