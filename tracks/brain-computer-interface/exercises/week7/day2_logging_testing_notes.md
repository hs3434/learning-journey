# Week 7 Day 22：日志系统与异常处理

## 1. 为什么需要日志？

没有日志的 BCI 系统：

```
# 脚本跑了两小时，突然崩溃
# 你只知道 "Error"，不知道在哪一步出错
# 是数据加载失败？滤波参数错误？分类器溢出？
# → 只能从头开始，加 print，重新跑两小时
```

有日志的 BCI 系统：

```
[2026-05-26 10:00:01] INFO  loader.load: Loading data from eeg_raw.fif
[2026-05-26 10:00:03] INFO  loader.load: Loaded 16 channels, 256Hz, 277.3s
[2026-05-26 10:00:03] INFO  preprocessor: Applying bandpass 1-40 Hz (FIR)
[2026-05-26 10:00:05] WARNING preprocessor: Channel Fp1 has high impedance (>10kΩ)
[2026-05-26 10:00:05] INFO  preprocessor: Applying notch 50/100 Hz
[2026-05-26 10:00:07] INFO  epocher: Found 284 events
[2026-05-26 10:00:08] INFO  epocher: Created 268 epochs (16 rejected)
[2026-05-26 10:00:08] INFO  decoder: Running LDA with 5-fold CV
[2026-05-26 10:00:10] INFO  decoder: Accuracy = 85.2%, ITR = 62.3 bits/min
```

### 打个比方

- 没有 log = 黑箱手术：病人出了问题，不知道哪个环节出错
- 有 log = 完整病历：每一步操作都有记录，回溯定位秒级完成

---

## 2. Python logging 模块

### 2.1 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 详细调试信息 | "Filter coefficients: b=[...], a=[...]" |
| INFO | 正常流程信息 | "Loaded 16 channels, 256Hz" |
| WARNING | 可疑但不致命 | "Channel Fp1 has high impedance" |
| ERROR | 功能受影响 | "ICA failed to converge after 200 iterations" |
| CRITICAL | 系统级故障 | "Cannot connect to EEG amplifier" |

### 2.2 基础配置

```python
import logging

# 简单配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('bci_pipeline.log'),  # 写文件
        logging.StreamHandler(),                    # 控制台输出
    ]
)

# 每个模块用自己的 logger
logger = logging.getLogger('bci.preprocessor')
logger.info("Applying bandpass filter")
logger.warning("Channel Fp1 has high impedance")
```

### 2.3 模块化日志

```python
# loader.py
logger = logging.getLogger('bci.loader')

class MNEDataLoader:
    def load(self, filepath):
        logger.info(f"Loading data from {filepath}")
        try:
            raw = mne.io.read_raw_fif(filepath, preload=True)
            logger.info(f"Loaded {len(raw.ch_names)} channels, "
                       f"{raw.info['sfreq']}Hz, {raw.times[-1]:.1f}s")
            return raw
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            raise

# preprocessor.py
logger = logging.getLogger('bci.preprocessor')

class Preprocessor:
    def process(self, raw):
        logger.info(f"Applying bandpass {self.config.l_freq}-{self.config.h_freq} Hz")
        filtered = raw.copy().filter(self.config.l_freq, self.config.h_freq)
        logger.debug(f"Filter method: {self.config.method}")
        return filtered
```

---

## 3. 异常处理

### 3.1 自定义异常层级

```python
class BCIPipelineError(Exception):
    """BCI Pipeline 基础异常"""
    pass

class DataLoadError(BCIPipelineError):
    """数据加载失败"""
    pass

class PreprocessError(BCIPipelineError):
    """预处理失败"""
    pass

class FilterError(PreprocessError):
    """滤波失败"""
    pass

class EpochError(BCIPipelineError):
    """Epoch 提取失败"""
    pass

class DecodeError(BCIPipelineError):
    """解码失败"""
    pass
```

### 3.2 异常处理策略

```python
class BCIPipeline:
    def run(self, filepath):
        try:
            self.data.raw = self.loader.load(filepath)
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            raise DataLoadError(f"EEG file not found: {filepath}")
        except ValueError as e:
            logger.error(f"Invalid file format: {e}")
            raise DataLoadError(f"Cannot parse {filepath}") from e
        
        try:
            self.data.filtered = self.preprocessor.process(self.data.raw)
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise PreprocessError(f"Filter failed") from e
        
        try:
            self.data.epochs = self.epocher.extract(self.data.filtered)
        except Exception as e:
            logger.warning(f"Epoch extraction had issues: {e}")
            # 降级处理：用更宽松的参数重试
            self.data.epochs = self.epocher.extract(
                self.data.filtered, reject=None
            )
```

### 3.3 优雅降级

BCI 系统的一个关键设计：**部分失败不应导致整体崩溃**。

```python
def run_with_fallback(self, filepath):
    """带降级策略的 Pipeline"""
    # 主方案
    try:
        return self._run_full_pipeline(filepath)
    except PreprocessError:
        logger.warning("Full preprocessing failed, trying minimal pipeline")
        # 降级：跳过 ICA
        return self._run_minimal_pipeline(filepath)
    except DecodeError:
        logger.warning("Decoding failed, returning preprocessing results only")
        # 降级：只返回预处理结果，不做解码
        return self.data
```

---

## 4. 结构化日志

### 4.1 JSON 日志（适合机器解析）

```python
import json_log_formatter

formatter = json_log_formatter.JSONFormatter()
handler = logging.FileHandler('bci_pipeline.json.log')
handler.setFormatter(formatter)

logger = logging.getLogger('bci')
logger.addHandler(handler)

# 输出：
# {"asctime": "2026-05-26 10:00:01", "levelname": "INFO", 
#  "name": "bci.loader", "message": "Loaded 16 channels"}
```

### 4.2 性能日志

```python
import time
import functools

def log_execution_time(func):
    """装饰器：记录函数执行时间"""
    logger = logging.getLogger('bci.performance')
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

# 使用
@log_execution_time
def apply_filter(raw, l_freq, h_freq):
    return raw.copy().filter(l_freq, h_freq)
```

---

## 5. 总结

| 概念 | 核心要点 |
|------|----------|
| 日志级别 | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| 模块化日志 | 每个模块 `getLogger(__name__)` |
| 自定义异常 | 分层异常类，精准定位问题 |
| 优雅降级 | 部分失败不崩溃，降级方案兜底 |
| 结构化日志 | JSON 格式，方便 ELK 分析 |
| 性能日志 | 装饰器记录函数耗时 |
