"""
Week 7 Day 2: Logging and Exception Handling
=============================================
日志系统、异常处理
"""
import logging
import numpy as np
from typing import Optional

# ============================================================
# 1. Logging 基础配置
# ============================================================
print("=" * 60)
print("1. Logging 基础配置")
print("=" * 60)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('bci.pipeline')
logger.info("Pipeline initialized")

# ============================================================
# 2. 多模块 Logger 配置
# ============================================================
print("\n" + "=" * 60)
print("2. 多模块 Logger 配置")
print("=" * 60)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """创建配置好的 logger"""
    log = logging.getLogger(name)
    log.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(name)s | %(levelname)s | %(message)s'
    ))
    log.addHandler(handler)

    return log

log_loader = setup_logger('bci.loader')
log_preproc = setup_logger('bci.preprocessor')
log_decode = setup_logger('bci.decoder')

log_loader.info("Loading EEG file: sample.fif")
log_preproc.warning("Channel Fp1 has high impedance (>20kΩ)")
log_decode.info("SSVEP detection started")

# ============================================================
# 3. 异常层次结构
# ============================================================
print("\n" + "=" * 60)
print("3. 异常层次结构")
print("=" * 60)

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

try:
    raise DataLoadError("Cannot open file: data.fif")
except BCIPipelineError as e:
    print(f"Caught pipeline error: {e}")
    print(f"Exception type: {type(e).__name__}")

try:
    raise PreprocessError("Filter failed: invalid cutoff frequency")
except BCIPipelineError as e:
    print(f"Caught: {type(e).__name__}: {e}")

# ============================================================
# 4. 异常链与上下文
# ============================================================
print("\n" + "=" * 60)
print("4. 异常链与上下文")
print("=" * 60)

def load_data_with_validation(filepath: str) -> np.ndarray:
    """带验证的数据加载"""
    try:
        if not filepath.endswith('.fif'):
            raise DataLoadError(f"Unsupported format: {filepath}")

        data = np.random.randn(16, 25600)

        if data.shape[0] < 1:
            raise DataLoadError("No channels loaded")

        return data

    except DataLoadError:
        print(f"DataLoadError: File validation failed for {filepath}")
        raise

try:
    load_data_with_validation("data.csv")
except DataLoadError as e:
    print(f"Final error: {e}")

# ============================================================
# 5. Graceful Degradation
# ============================================================
print("\n" + "=" * 60)
print("5. Graceful Degradation (降级策略)")
print("=" * 60)

def process_with_fallback(data: np.ndarray, use_ica: bool = True) -> dict:
    """带降级策略的处理"""
    result = {}

    try:
        result['filtered'] = data.mean(axis=1)
    except Exception as e:
        logging.warning(f"Filter failed: {e}, using raw data")
        result['filtered'] = data

    if use_ica:
        try:
            result['ica_cleaned'] = result['filtered'] * 0.95
        except Exception as e:
            logging.warning(f"ICA failed: {e}, skipping ICA")
            result['ica_cleaned'] = result['filtered']

    return result

data = np.random.randn(16, 25600)
result = process_with_fallback(data, use_ica=True)
print(f"Result keys: {list(result.keys())}")

print("\n✅ Day 2 完成!")