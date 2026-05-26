# Week 7 Day 21：模块化设计与配置管理

## 1. 为什么需要模块化？

Week 1-6 的代码是"科研风格"——一个脚本跑完所有步骤：

```python
# 科研风格：一个文件搞定一切
raw = mne.io.read_raw_fif('data.fif', preload=True)
raw.filter(1, 40)
raw.notch_filter([50, 100])
events = mne.find_events(raw)
epochs = mne.Epochs(raw, events, tmin=-0.2, tmax=0.5)
clf = LDA()
scores = cross_val_score(clf, X, y, cv=5)
print(f'Accuracy: {scores.mean():.2%}')
```

**问题**：
- 改一个滤波参数，要翻遍整个脚本找
- 换一个分类器，要改好几处
- 别人拿到代码，不知道从哪开始读
- 数据格式变了，整个脚本崩溃

**模块化 = 把大脚本拆成小积木**，每个积木只做一件事：

```
bci_pipeline/
├── config.py        # 配置管理
├── loader.py        # 数据加载
├── preprocessor.py  # 预处理（滤波/ICA）
├── epocher.py       # Epoch 提取
├── decoder.py       # 解码分类
├── exporter.py      # 数据导出
├── reporter.py      # 报告生成
└── pipeline.py      # 主编排器
```

### 打个比方

- 科研代码 = 一锅炖（所有食材扔进去）
- 模块化 = 自助餐（每道菜独立，自取组合）

---

## 2. 模块化设计原则

### 2.1 单一职责原则 (SRP)

每个模块只做一件事：

| 模块 | 职责 | 不做的事 |
|------|------|----------|
| loader | 加载数据 | 不做滤波 |
| preprocessor | 滤波/去伪迹 | 不做分类 |
| epocher | 提取 Epoch | 不做可视化 |
| decoder | 分类解码 | 不做导出 |

### 2.2 依赖注入

模块间通过接口通信，不直接依赖具体实现：

```python
# 差：硬编码依赖
class Preprocessor:
    def __init__(self):
        self.loader = MNELoader()  # 绑死了 MNE
    
# 好：依赖注入
class Preprocessor:
    def __init__(self, loader):  # 传入任何 loader
        self.loader = loader
```

### 2.3 接口抽象

```python
from abc import ABC, abstractmethod

class DataLoader(ABC):
    """数据加载器抽象接口"""
    
    @abstractmethod
    def load(self, filepath: str) -> Raw:
        """加载 EEG 数据"""
        pass
    
    @abstractmethod
    def get_info(self) -> dict:
        """获取数据信息"""
        pass

class MNEDataLoader(DataLoader):
    """MNE 实现的具体加载器"""
    def load(self, filepath):
        return mne.io.read_raw_fif(filepath, preload=True)
    
    def get_info(self):
        return {'n_channels': len(self.raw.ch_names), ...}

class EEGLABLoader(DataLoader):
    """EEGLAB .set 格式加载器"""
    def load(self, filepath):
        return mne.io.read_raw_eeglab(filepath, preload=True)
```

---

## 3. 配置管理

### 3.1 为什么用配置文件？

```python
# 差：参数散落在代码各处
raw.filter(1, 40)                    # 第10行
raw.notch_filter([50, 100])          # 第15行
epochs = mne.Epochs(raw, events,     
                    tmin=-0.2,        # 第22行
                    tmax=0.5)         # 第23行
clf = LDA()                           # 第30行
```

```yaml
# 好：所有参数集中管理
filter:
  l_freq: 1.0
  h_freq: 40.0
  notch_freqs: [50, 100]
  
epoch:
  tmin: -0.2
  tmax: 0.5
  baseline: [null, 0]
  
decode:
  method: lda
  cv_folds: 5
```

### 3.2 Dataclass 配置

```python
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

@dataclass
class FilterConfig:
    l_freq: float = 1.0
    h_freq: float = 40.0
    notch_freqs: List[float] = field(default_factory=lambda: [50.0, 100.0])
    method: str = 'fir'

@dataclass
class EpochConfig:
    tmin: float = -0.2
    tmax: float = 0.5
    baseline: Tuple[Optional[float], Optional[float]] = (None, 0)
    reject: Optional[dict] = field(default_factory=lambda: {'eeg': 100e-6})

@dataclass  
class DecodeConfig:
    method: str = 'lda'
    cv_folds: int = 5
    
@dataclass
class PipelineConfig:
    """完整 Pipeline 配置"""
    filter: FilterConfig = field(default_factory=FilterConfig)
    epoch: EpochConfig = field(default_factory=EpochConfig)
    decode: DecodeConfig = field(default_factory=DecodeConfig)
    output_dir: str = './output'
    verbose: bool = True
```

### 3.3 YAML 加载器

```python
import yaml
from dataclasses import asdict

class ConfigManager:
    """配置管理器：加载/保存/验证配置"""
    
    @staticmethod
    def from_yaml(filepath: str) -> PipelineConfig:
        """从 YAML 加载配置"""
        with open(filepath) as f:
            data = yaml.safe_load(f)
        
        # 递归构造嵌套 dataclass
        filter_cfg = FilterConfig(**data.get('filter', {}))
        epoch_cfg = EpochConfig(**data.get('epoch', {}))
        decode_cfg = DecodeConfig(**data.get('decode', {}))
        
        return PipelineConfig(
            filter=filter_cfg,
            epoch=epoch_cfg,
            decode=decode_cfg,
            output_dir=data.get('output_dir', './output'),
        )
    
    @staticmethod
    def to_yaml(config: PipelineConfig, filepath: str):
        """保存配置到 YAML"""
        data = asdict(config)
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    
    @staticmethod
    def validate(config: PipelineConfig) -> List[str]:
        """验证配置合法性"""
        errors = []
        if config.filter.l_freq >= config.filter.h_freq:
            errors.append("l_freq must be less than h_freq")
        if config.filter.l_freq <= 0:
            errors.append("l_freq must be positive")
        if config.epoch.tmin >= config.epoch.tmax:
            errors.append("tmin must be less than tmax")
        return errors
```

---

## 4. 模块间的数据流

### 4.1 Pipeline 数据容器

```python
@dataclass
class PipelineData:
    """Pipeline 各阶段的数据容器"""
    raw: Optional[mne.io.Raw] = None
    filtered: Optional[mne.io.Raw] = None
    events: Optional[np.ndarray] = None
    event_id: Optional[dict] = None
    epochs: Optional[mne.Epochs] = None
    evoked: Optional[dict] = None
    scores: Optional[dict] = None
    figures: dict = field(default_factory=dict)
```

### 4.2 主编排器

```python
class BCIPipeline:
    """BCI Pipeline 主编排器"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.data = PipelineData()
        self.loader = MNEDataLoader()
        self.preprocessor = Preprocessor(config.filter)
        self.epocher = Epocher(config.epoch)
        self.decoder = Decoder(config.decode)
        self.exporter = Exporter(config.output_dir)
    
    def run(self, filepath: str) -> PipelineData:
        """一键运行完整 Pipeline"""
        self.data.raw = self.loader.load(filepath)
        self.data.filtered = self.preprocessor.process(self.data.raw)
        self.data.events = self.epocher.find_events(self.data.filtered)
        self.data.epochs = self.epocher.extract(self.data.filtered, self.data.events)
        self.data.scores = self.decoder.decode(self.data.epochs)
        return self.data
```

---

## 5. 总结

| 概念 | 核心要点 |
|------|----------|
| 模块化 | 每个模块只做一件事（SRP） |
| 依赖注入 | 模块通过接口通信，不硬编码依赖 |
| 抽象接口 | ABC 定义接口，多实现可替换 |
| Dataclass 配置 | 类型安全 + 默认值 + 可序列化 |
| YAML 配置 | 人类可读，版本控制友好 |
| 配置验证 | 运行前检查参数合法性 |
| 数据容器 | PipelineData 贯穿各模块 |
| 主编排器 | BCIPipeline 串联所有模块 |
