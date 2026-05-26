# Week 7 Day 23：单元测试与集成测试

## 1. 为什么 BCI 代码需要测试？

BCI 信号处理的 bug 通常**不会直接报错**——它只是让准确率悄悄从 85% 降到 75%。

```
# 这段代码有 bug，但不报错
X = epochs.get_data()  # shape: (n_epochs, n_channels, n_times)
features = X.mean(axis=1)  # BUG: 应该是 axis=2

# 结果：特征维度错误，分类器"强行"运行，准确率降低
# 但你以为"只是这个被试表现差"
```

**没有测试 = bug 寄生在结果里，你永远不知道答案错了。**

### 打个比方

- 没有测试 = 盲人开车：你以为在直行，其实已经偏了
- 有测试 = 导航仪：每走一步都有纠偏提醒

---

## 2. 测试分层

```
┌───────────────────────────┐
│    End-to-End Tests        │  ← 完整 Pipeline 从头到尾
│    (慢，覆盖完整流程)        │
├───────────────────────────┤
│    Integration Tests       │  ← 多模块协作
│    (中速，模块间接口)        │
├───────────────────────────┤
│    Unit Tests              │  ← 单个函数/类
│    (快，精确到函数)          │
└───────────────────────────┘
```

---

## 3. 单元测试

### 3.1 pytest 基础

```python
# tests/test_preprocessor.py
import pytest
import numpy as np
from bci.preprocessor import Preprocessor, FilterConfig

class TestPreprocessor:
    """Preprocessor 单元测试"""
    
    @pytest.fixture
    def sample_data(self):
        """测试夹具：生成合成 EEG 数据"""
        fs = 256
        t = np.arange(int(fs * 5)) / fs
        # 10Hz alpha + 50Hz powerline + noise
        data = 30 * np.sin(2 * np.pi * 10 * t) + \
               20 * np.sin(2 * np.pi * 50 * t) + \
               np.random.randn(len(t)) * 5
        return data, fs
    
    def test_bandpass_removes_high_freq(self, sample_data):
        """带通滤波应移除高频分量"""
        data, fs = sample_data
        config = FilterConfig(l_freq=1.0, h_freq=40.0)
        proc = Preprocessor(config)
        
        filtered = proc.bandpass(data, fs)
        
        # 验证：50Hz 分量应大幅衰减
        from scipy.signal import welch
        _, psd = welch(filtered, fs, nperseg=512)
        freqs_idx = np.arange(len(psd)) * fs / 1024
        
        power_50hz = psd[np.argmin(np.abs(freqs_idx - 50))]
        power_10hz = psd[np.argmin(np.abs(freqs_idx - 10))]
        
        assert power_50hz < power_10hz * 0.01  # 50Hz 应比 10Hz 低 100 倍
    
    def test_notch_removes_powerline(self, sample_data):
        """Notch 滤波应移除 50Hz"""
        data, fs = sample_data
        proc = Preprocessor(FilterConfig())
        
        notched = proc.notch(data, 50, fs)
        
        _, psd = welch(notched, fs, nperseg=512)
        freqs_idx = np.arange(len(psd)) * fs / 1024
        power_50hz = psd[np.argmin(np.abs(freqs_idx - 50))]
        
        assert power_50hz < 1.0  # 50Hz 功率应极低
    
    def test_invalid_freq_raises_error(self):
        """非法频率应抛出异常"""
        config = FilterConfig(l_freq=50.0, h_freq=10.0)  # 低频 > 高频
        
        with pytest.raises(ValueError, match="l_freq must be less"):
            config.validate()
```

### 3.2 参数化测试

```python
@pytest.mark.parametrize("l_freq,h_freq,expected", [
    (1, 40, True),      # 合法
    (0.5, 100, True),   # 合法
    (50, 10, False),    # 低频 > 高频
    (0, 40, False),     # 低频 = 0
    (-1, 40, False),    # 负频率
])
def test_filter_config_validation(l_freq, h_freq, expected):
    """参数化测试：各种滤波参数组合"""
    config = FilterConfig(l_freq=l_freq, h_freq=h_freq)
    errors = config.validate()
    is_valid = len(errors) == 0
    assert is_valid == expected
```

### 3.3 Mock 测试

```python
from unittest.mock import MagicMock, patch

class TestPipelineWithMock:
    """使用 Mock 隔离外部依赖"""
    
    def test_pipeline_calls_loader(self):
        """Pipeline 应调用 loader.load()"""
        mock_loader = MagicMock()
        mock_loader.load.return_value = MagicMock()
        
        pipeline = BCIPipeline(config=MagicMock(), loader=mock_loader)
        pipeline.run('test.fif')
        
        mock_loader.load.assert_called_once_with('test.fif')
    
    @patch('mne.io.read_raw_fif')
    def test_loader_error_handling(self, mock_read):
        """加载失败应抛出 DataLoadError"""
        mock_read.side_effect = FileNotFoundError("No file")
        
        loader = MNEDataLoader()
        with pytest.raises(DataLoadError):
            loader.load('nonexistent.fif')
```

---

## 4. 集成测试

### 4.1 模块间接口测试

```python
class TestPreprocessorEpocherIntegration:
    """Preprocessor → Epocher 接口测试"""
    
    @pytest.fixture
    def pipeline_data(self):
        """准备经过预处理的数据"""
        raw = create_synthetic_raw(n_channels=16, duration=10, fs=256)
        proc = Preprocessor(FilterConfig(l_freq=1, h_freq=40))
        filtered = proc.process(raw)
        return filtered
    
    def test_preprocessor_output_compatible_with_epocher(self, pipeline_data):
        """Preprocessor 输出应能直接传入 Epocher"""
        epocher = Epocher(EpochConfig())
        events = mne.find_events(pipeline_data)
        epochs = epocher.extract(pipeline_data, events)
        
        assert epochs is not None
        assert len(epochs) > 0
```

### 4.2 端到端测试

```python
class TestEndToEnd:
    """完整 Pipeline 测试"""
    
    def test_full_pipeline_with_synthetic_data(self, tmp_path):
        """合成数据 → 完整 Pipeline → 有结果输出"""
        # 1. 创建合成数据
        raw = create_synthetic_raw()
        data_path = tmp_path / 'synthetic.fif'
        raw.save(data_path, overwrite=True)
        
        # 2. 运行 Pipeline
        config = PipelineConfig(output_dir=str(tmp_path))
        pipeline = BCIPipeline(config)
        result = pipeline.run(str(data_path))
        
        # 3. 验证结果
        assert result.raw is not None
        assert result.filtered is not None
        assert result.epochs is not None
        assert result.scores is not None
        assert 'accuracy' in result.scores
```

---

## 5. 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest --cov=bci --cov-report=html tests/

# 目标覆盖率
# - 核心模块 (preprocessor, decoder): > 90%
# - 数据加载/导出: > 80%
# - GUI 相关: > 50% (UI 测试成本高)
```

---

## 6. 总结

| 概念 | 核心要点 |
|------|----------|
| 测试金字塔 | Unit > Integration > E2E |
| pytest | fixture + parametrize + mock |
| 参数化测试 | 一套逻辑，多组输入 |
| Mock | 隔离外部依赖，专注测试逻辑 |
| 合成数据 | 无需真实 EEG，快速跑测试 |
| 覆盖率 | 核心模块 > 90%，整体 > 80% |
