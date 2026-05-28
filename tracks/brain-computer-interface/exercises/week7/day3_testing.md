# Week 7 Day 3: Unit Testing and CI

## 核心概念

### 1. 测试金字塔

```
        /\
       /  \    E2E Tests
      /____\   (少量、慢)
     /      \
    /        \  Integration Tests
   /__________\ (中量、中速)
  /            \
 /______________\ Unit Tests
 (大量、快)
```

### 2. pytest 基本用法

```python
import pytest
import numpy as np

def test_bandpass_filter():
    data = np.random.randn(16, 2560)
    filtered = bandpass_filter(data, fs=256, lowcut=0.5, highcut=40)

    assert filtered.shape == data.shape
    assert not np.isnan(filtered).any()
```

### 3. Fixture

```python
@pytest.fixture
def sample_eeg_data():
    """创建样本 EEG 数据"""
    return np.random.randn(16, 2560)

def test_filter_shape(sample_eeg_data):
    filtered = bandpass_filter(sample_eeg_data, fs=256, lowcut=0.5, highcut=40)
    assert filtered.shape == sample_eeg_data.shape
```

### 4. 参数化测试

```python
filter_params = [
    (0.5, 40),
    (1, 30),
    (2, 20),
]

@pytest.mark.parametrize("lowcut,highcut", filter_params)
def test_bandpass_parametrized(lowcut, highcut):
    data = np.random.randn(16, 2560)
    filtered = bandpass_filter(data, fs=256, lowcut=lowcut, highcut=highcut)
    assert filtered.shape == data.shape
```

### 5. Mock

```python
from unittest.mock import MagicMock

def test_pipeline_with_mock():
    mock_loader = MagicMock()
    mock_loader.load.return_value = np.random.randn(16, 2560)

    pipeline = Pipeline(mock_loader)
    result = pipeline.run()

    assert result.shape == (16, 2560)
    mock_loader.load.assert_called_once()
```

### 6. CI 配置

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install pytest pytest-cov
          pytest tests/ --cov=bci --cov-report=xml
```

## 测试覆盖率

```bash
pytest tests/ --cov=bci --cov-report=html
```

## 练习要点

1. 掌握 pytest 基本用法
2. 学会使用 fixture
3. 理解参数化测试
4. 了解 CI 配置

## 参考资料

- [pytest 文档](https://docs.pytest.org/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [GitHub Actions](https://docs.github.com/en/actions)