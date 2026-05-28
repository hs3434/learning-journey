# Week 7 Day 2: Logging and Exception Handling

## 核心概念

### 1. Logging 级别

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 调试信息 | `Filter coefficients: b=[0.1, 0.2]` |
| INFO | 正常信息 | `Loaded 16 channels, 256Hz` |
| WARNING | 警告 | `Channel Fp1 has high impedance` |
| ERROR | 错误 | `ICA failed to converge` |
| CRITICAL | 严重错误 | `Cannot connect to amplifier` |

### 2. Logging 配置

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('bci.pipeline')
logger.info("Pipeline initialized")
```

### 3. 异常层次结构

```python
class BCIPipelineError(Exception):
    """Pipeline 基础异常"""
    pass

class DataLoadError(BCIPipelineError):
    """数据加载异常"""
    pass

class PreprocessError(BCIPipelineError):
    """预处理异常"""
    pass

class DecodeError(BCIPipelineError):
    """解码异常"""
    pass
```

### 4. 异常处理

```python
try:
    raw = mne.io.read_raw_fif(filepath, preload=True)
except FileNotFoundError as e:
    logger.error(f"File not found: {filepath}")
    raise DataLoadError(f"Cannot load {filepath}") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise BCIPipelineError(str(e)) from e
```

### 5. Graceful Degradation

```python
def process_with_fallback(data, use_ica=True):
    result = {}

    try:
        result['filtered'] = apply_filter(data)
    except Exception as e:
        logger.warning(f"Filter failed: {e}")
        result['filtered'] = data

    if use_ica:
        try:
            result['ica_cleaned'] = apply_ica(result['filtered'])
        except Exception as e:
            logger.warning(f"ICA failed: {e}")
            result['ica_cleaned'] = result['filtered']

    return result
```

### 6. 多模块 Logger

```python
# 每个模块创建自己的 logger
logger = logging.getLogger(__name__)

# bci/loader/__init__.py
loader_logger = logging.getLogger('bci.loader')

# bci/preprocessor/__init__.py
preproc_logger = logging.getLogger('bci.preprocessor')
```

## 练习要点

1. 掌握 logging 配置
2. 理解异常层次
3. 学会 graceful degradation

## 参考资料

- [Python logging](https://docs.python.org/3/library/logging.html)
- [ Logging best practices](https://docs.python.org/3/howto/logging-cookbook.html)