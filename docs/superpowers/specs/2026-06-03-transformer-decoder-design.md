# Transformer 解码器 — 设计稿

**日期**：2026-06-03
**状态**：待审阅
**目标**：在 BCI 解码框架中新增 `Transformer` 解码器，作为可拔插插件。

## 背景与目标

项目当前有 4 个解码器：`lda` / `ssvep` / `fbcca` / `cnn`，通过 `@register` 装饰器注册到 `bci/decoder/__init__.py` 的注册表。新增 Transformer 解码器，沿用现有 ABC 接口。

**核心要求**：
- 遵循可拔插、模块化、接口标准化的设计原则
- 与现有 `CNNDecoder` 共享 PyTorch 可选依赖
- 保持零新增第三方依赖

## 设计决策

| 维度 | 决策 | 理由 |
|------|------|------|
| 架构 | 多尺度 CNN 前端 + Transformer 编码器 | 解决 EEG 全局/局部信息矛盾 |
| 输入表示 | 时间步作为 token | 避免 patch 切分破坏局部结构 |
| 注意力 | 手写多头自注意力 | 零新依赖 |
| 注册方式 | `@register('transformer')` | 沿用现有 ABC 模式 |
| 保存格式 | `torch.save/load` | 与 `CNNDecoder` 一致 |

## 架构

### 数据流

```
输入: (B, n_channels, n_times) EEG epochs  = (B, 64, 1000)
   ↓
[_CNNFrontend]
  ├─ Conv1d (in=64, out=11, k=15, padding='same'): (B, 11, 1000)  ← 短时
  ├─ Conv1d (in=64, out=11, k=25, padding='same'): (B, 11, 1000)  ← 中时
  ├─ Conv1d (in=64, out=10, k=50, padding='same'): (B, 10, 1000)  ← 长时
  ├─ Concat: (B, 32, 1000)
  ├─ Conv1d (in=32, out=32, k=1) 通道混合: (B, 32, 1000)
  └─ AvgPool1d(kernel=20, stride=20) 降采样: (B, 32, 50)
   ↓
Permute → (B, 50, 32)  ← 时间步作为序列
   ↓
Linear Projection → d_model=64: (B, 50, 64)
   ↓
+ CLS Token + 1D Positional Encoding: (B, 51, 64)  ← Transformer 输入
   ↓
[N × Transformer Blocks]                              ← sequence-to-sequence
   每个 block 保持形状不变：输入 (B, 51, 64) → 输出 (B, 51, 64)
   ↓
Transformer Blocks 输出: (B, 51, 64)
   ↓
取出 CLS 位置 ([:, 0, :]): (B, 64)                   ← 步骤 1
   ↓
Final LayerNorm: (B, 64)                              ← 步骤 2
   ↓
Linear Classifier: (B, n_classes)                     ← 步骤 3
```

### Transformer 后处理（CLS 提取）详解

Transformer 是 sequence-to-sequence 操作，输入输出形状相同。**分类需要从 51 个时间步中提取一个固定大小的向量**，标准做法是取 CLS token：

```
Transformer Blocks 输出: (B, 51, 64)
   ↓
[步骤 1] 切片取出 CLS（位置 0）
   x_cls = x[:, 0, :]  # 丢弃 t1~t50，保留 CLS
   形状: (B, 51, 64) → (B, 64)
   ↓
[步骤 2] Final LayerNorm
   x_cls = nn.LayerNorm(64)(x_cls)
   形状: (B, 64) → (B, 64)
   作用: 稳定分类头输入分布
   ↓
[步骤 3] Linear 分类头
   logits = nn.Linear(64, n_classes)(x_cls)
   形状: (B, 64) → (B, n_classes)
```

### Transformer Block 内部结构

每个 Block 是 **Pre-LN** 架构（先 LN 再计算，比 Post-LN 训练更稳定）：

```
输入: (B, 51, 64)
   ↓
[1] LayerNorm: (B, 51, 64)        ← Pre-LN（在 MHA 之前）
   ↓
[2] 多头自注意力（手写 nn.Module）
   ├─ Q = Linear(64, 64)(x)        # (B, 51, 64)
   ├─ K = Linear(64, 64)(x)        # (B, 51, 64)
   ├─ V = Linear(64, 64)(x)        # (B, 51, 64)
   ├─ Split into 4 heads: (B, 4, 51, 16)
   ├─ Attention = softmax(QK^T / sqrt(16))   # (B, 4, 51, 51)
   ├─ Concat heads: (B, 51, 64)
   └─ Output projection: Linear(64, 64)       # (B, 51, 64)
   ↓
[3] 残差连接（Residual）: x + attn_out
   形状: (B, 51, 64)
   ↓
[4] LayerNorm: (B, 51, 64)        ← Pre-LN（在 FFN 之前）
   ↓
[5] FFN（前馈网络）
   ├─ Linear(64, 256)              # (B, 51, 256)  # 4×d_model
   ├─ GELU / ReLU
   ├─ Dropout
   └─ Linear(256, 64)              # (B, 51, 64)
   ↓
[6] 残差连接: x + ffn_out
   形状: (B, 51, 64)
   ↓
Block 输出: (B, 51, 64)  ← 输入输出形状相同
```

**Pre-LN 与 Post-LN 对比**：

```
Pre-LN（采用）                Post-LN（不采用）
                                 
x → LN → MHA → +              x → MHA → + → LN
    ↘___________↗                ↗___________↘
                                 
x → LN → FFN → +              x → FFN → + → LN
    ↘___________↗                ↗___________↘
```

Pre-LN 的优势：残差路径上无 LayerNorm，梯度流畅，训练更稳定；适合深层 / 小样本场景。

**Dropout 位置**：
- MHA 输出后（`attn_dropout`）
- FFN 输出后（`ffn_dropout`）
- 默认 dropout=0.2

### 模块拆分

```
bci/decoder/transformer.py  (~200 行)

_MultiHeadSelfAttention     手写多头自注意力（~50 行）
_FeedForward                FFN 两层 MLP（~10 行）
_TransformerBlock           Pre-LN encoder block（~30 行）
_CNNFrontend                多尺度时间卷积 + 通道混合 + 降采样（~50 行）
_EEGTransformer             Linear 投影 + Encoder 堆叠 + 分类头（~60 行）
TransformerDecoder          Decoder ABC 包装（~80 行）
```

## 接口设计

### `TransformerDecoder` 公共 API

```python
class TransformerDecoder(Decoder):
    def __init__(
        self,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 3,
        n_filters: int = 32,
        temporal_kernels: Tuple[int, ...] = (15, 25, 50),
        downsample_factor: int = 20,
        dropout: float = 0.2,
        epochs: int = 50,
        lr: float = 5e-4,
        weight_decay: float = 1e-4,
        device: str = 'cpu',
    ) -> None:
        ...

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'TransformerDecoder':
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        ...

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        ...

    def save(self, path: str | Path) -> None:
        ...

    @classmethod
    def load(cls, path: str | Path) -> 'TransformerDecoder':
        ...
```

### 依赖门控

```python
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_OK = True
except ImportError:
    TORCH_OK = False

if not TORCH_OK:
    _EEGCNN = None
    TransformerDecoder = None  # type: ignore
```

未安装 PyTorch 时不报错，但注册表中 `'transformer'` 不可用——与 `CNNDecoder` 行为一致。

## 注册集成

### `bci/decoder/__init__.py` 修改

文件末尾追加：

```python
@register('transformer')
class _TransformerDecoder:
    @staticmethod
    def create(**kw):
        from bci.decoder.transformer import TransformerDecoder
        return TransformerDecoder(**kw)
```

### `bci/gui/widgets/decode_page.py` 修改

```python
# 第 28 行
self._method.addItems(['lda', 'ssvep', 'fbcca', 'cnn', 'transformer'])
```

## 超参数

| 参数 | 默认值 | 范围 | 备注 |
|------|--------|------|------|
| `d_model` | 64 | [32, 128] | 嵌入维度 |
| `n_heads` | 4 | [1, 8] | head_dim = d_model / n_heads |
| `n_layers` | 3 | [1, 6] | 防止过拟合 |
| `n_filters` | 32 | [16, 64] | CNN 前端输出通道 |
| `temporal_kernels` | (15, 25, 50) | — | 多尺度时间卷积核 |
| `downsample_factor` | 20 | [5, 50] | 时间维度降采样率 |
| `dropout` | 0.2 | [0.0, 0.5] | |
| `epochs` | 50 | [10, 200] | 训练轮数 |
| `lr` | 5e-4 | [1e-5, 1e-2] | |
| `weight_decay` | 1e-4 | [0.0, 1e-2] | AdamW |

## 文件清单

### 新增

| 文件 | 行数 | 用途 |
|------|------|------|
| `bci/decoder/transformer.py` | ~200 | 核心实现 |
| `bci/tests/test_transformer.py` | ~150 | 单元测试 |
| `bci/tests/test_transformer_e2e.py` | ~80 | 集成测试 |

### 修改

| 文件 | 改动 |
|------|------|
| `bci/decoder/__init__.py` | 追加 `@register('transformer')`（~10 行） |
| `bci/gui/widgets/decode_page.py` | `addItems` 列表加 `'transformer'`（1 行） |

## 测试策略

| 类型 | 内容 |
|------|------|
| **单元：MHA** | 多头拆分、注意力权重、缩放因子 |
| **单元：TransformerBlock** | Pre-LN、Residual、维度保持 |
| **单元：CNN 前端** | 多尺度输出拼接、降采样形状 |
| **单元：EEGTransformer** | CLS token、Position encoding、输出维度 |
| **单元：边界** | 通道/时间维度不匹配 |
| **集成：save/load** | 往返预测一致性 |
| **集成：decode()** | 跑通 `decode(method='transformer')` 端到端流程 |
| **基准：vs CNNDecoder** | 同一数据精度 + 速度对比 |

## 边界处理

| 情况 | 处理 |
|------|------|
| `n_times < downsample_factor` | 抛 `ValueError` |
| `n_times` 不是 `downsample_factor` 整数倍 | 自动截断（floor） |
| `n_classes < 2` | 抛 `ValueError` |
| PyTorch 未安装 | `TransformerDecoder` 为 `None`，注册表查不到（与 CNN 一致） |
| `n_heads` 不能整除 `d_model` | 抛 `ValueError` |

## 训练细节

- **优化器**：AdamW
- **Loss**：CrossEntropyLoss
- **批大小**：full-batch（BCI 数据量小）
- **数据增强**：不在初版中实现，保持简单
- **学习率调度**：不在初版中实现
- **早停**：不在初版中实现

## 风险与权衡

| 风险 | 缓解 |
|------|------|
| BCI 小样本易过拟合 | dropout=0.2、n_layers=3、强正则 |
| Transformer 训练不稳定 | Pre-LN、lr=5e-4、AdamW |
| 输入维度不一致 | 自动 padding/截断 + 边界校验 |
| CNN 前端参数量 | n_filters=32，控制总参数量 < 100K |

## 后续扩展（不在本次实现范围）

- 数据增强（时间抖动、通道掩码）
- 跨被试预训练
- 注意力权重可视化
- 与 `CNNDecoder` 模型蒸馏
- 替换为 Conformer 风格架构

## 设计原则遵守

- **单一职责**：每个模块一个清晰目的
- **接口隔离**：`Decoder` ABC 统一接口
- **依赖倒置**：高层（`decode()`）不依赖具体实现
- **开闭原则**：新增解码器无需修改现有代码（除了注册表 + GUI 下拉框）
