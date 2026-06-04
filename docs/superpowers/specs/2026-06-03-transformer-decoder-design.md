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
| 架构 | 多尺度 CNN 前端 + GPT 风格 Transformer 解码器 | 解决 EEG 全局/局部信息矛盾 |
| 位置编码 | **RoPE**（旋转位置编码） | 在 MHA 内部编码，外推能力强 |
| 注意力 | **单向因果**（causal mask） | 参考 GPT 架构，模拟时序因果性 |
| 分类方式 | **无 CLS，逐位置分类头，取最后位置** | GPT 风格，最后位置汇聚全序列信息 |
| 依赖 | 手写多头自注意力 + RoPE | 零新依赖 |
| 注册方式 | `@register('transformer')` | 沿用现有 ABC 模式 |
| 保存格式 | `torch.save/load` | 与 `CNNDecoder` 一致 |

**参考架构**：GPT（decoder-only Transformer） + 时序分类微调。

## 架构

### 数据流（GPT 风格）

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
[N × Decoder Blocks（带 RoPE + Causal Mask）]
   每个 block 保持形状：输入 (B, 50, 64) → 输出 (B, 50, 64)
   ↓
逐位置 Linear(64 → n_classes): (B, 50, n_classes)
   ↓
取最后位置 ([:, -1, :]): (B, n_classes)   ← GPT 风格：最后位置预测
```

### Decoder Block 内部结构（Pre-LN + Causal MHA + RoPE）

```
输入: (B, 50, 64)
   ↓
[1] LayerNorm: (B, 50, 64)        ← Pre-LN
   ↓
[2] Causal Multi-Head Self-Attention with RoPE
   ├─ Q = Linear(64, 64)(x)        # (B, 50, 64)
   ├─ K = Linear(64, 64)(x)        # (B, 50, 64)
   ├─ V = Linear(64, 64)(x)        # (B, 50, 64)
   ├─ Split into 4 heads: (B, 4, 50, 16)
   ├─ RoPE: rotate Q, K by position
   │   Q' = RoPE(Q, pos)
   │   K' = RoPE(K, pos)
   ├─ Causal Mask: 上三角置 -inf
   │   attention_mask[j, i] = -inf if i > j
   ├─ Attention = softmax(Q'K'^T / sqrt(16) + mask)   # (B, 4, 50, 50)
   ├─ Concat heads: (B, 50, 64)
   └─ Output projection: Linear(64, 64)                # (B, 50, 64)
   ↓
[3] 残差连接: x + attn_out
   形状: (B, 50, 64)
   ↓
[4] LayerNorm: (B, 50, 64)        ← Pre-LN
   ↓
[5] FFN（前馈网络）
   ├─ Linear(64, 256)              # (B, 50, 256)  # 4×d_model
   ├─ GELU
   ├─ Dropout
   └─ Linear(256, 64)              # (B, 50, 64)
   ↓
[6] 残差连接: x + ffn_out
   形状: (B, 50, 64)
   ↓
Block 输出: (B, 50, 64)  ← 输入输出形状相同
```

### Causal Mask 详解

```
位置:  0    1    2    3   ...   49
       ↑    ↑    ↑    ↑         ↑
mask =  0   -inf -inf -inf      -inf
       ↓
       0    0   -inf -inf      -inf
       ↓    ↓
       0    0    0   -inf      -inf
       ↓    ↓    ↓
       ...  0    0    0       -inf
       ↓    ↓    ↓    ↓
       0    0    0    0    ...   0
       ↓    ↓    ↓    ↓         ↓
attn[0,0] attn[0,1] attn[0,2] ...  # 位置 0 只能看自己
attn[1,0] attn[1,1] attn[1,2] ...  # 位置 1 能看 0 和 1
...                                  # 位置 49 能看全部
```

**为什么因果 mask 在分类中也合理**：
- EEG 时间序列有天然因果性：未来的信号不能影响过去
- 强制模型用过去信息预测当前 / 未来
- GPT 风格 = 因果语言模型 + 分类微调

### RoPE 旋转位置编码

**传统 1D PE（不采用）**：
```
embedding[i] + PE[i]  # 加法
```

**RoPE（采用）**：
```
对 Q, K 向量按位置角度旋转
Q'[i] = R(i) · Q[i]
K'[i] = R(i) · K[i]
其中 R(i) 是依赖于位置 i 的旋转矩阵
```

**RoPE 优势**：
- 通过 Q·K 内的点积自然编码相对位置
- 不增加参数量
- 长度外推能力强（训练 50 步可测试更长的序列）
- 现代 LLM 标配（LLaMA、Mistral、GPT-NeoX）

**简化实现**（d=2 例子）：
```
位置 0: 角度 = 0,    R = [[1, 0], [0, 1]]     # 单位旋转
位置 1: 角度 = θ,    R = [[cosθ, -sinθ], [sinθ, cosθ]]
位置 2: 角度 = 2θ,   R = [[cos2θ, -sin2θ], [sin2θ, cos2θ]]
...
```

**d_model=64 实现**：将 64 维分成 32 对，每对旋转不同角度：
```
θ_i = 1 / (10000^(2i/d))  for i in [0, 16)
位置 m 的旋转角: m * θ_i
```

### 分类头（GPT 风格）

```
Transformer 输出: (B, 50, 64)
   ↓
逐位置 Linear(64 → n_classes)
   每个位置独立映射：(B, 50, 64) → (B, 50, n_classes)
   ↓
取最后位置 [:, -1, :]
   (B, 50, n_classes) → (B, n_classes)
   ↓
CrossEntropyLoss(y, logits)
```

**为什么取最后位置**：
- 因果 mask 下，最后位置能看到全部 50 个时间步
- 最后位置的输出汇聚了整段序列的因果信息
- 与 GPT 自回归预测"下一个 token"的逻辑一致

### 模块拆分

```
bci/decoder/transformer.py  (~220 行)

_RotaryPositionalEmbedding  RoPE 旋转编码（~30 行）
_CausalMask                 因果 mask 生成（~10 行）
_CausalMHA                  Causal Multi-Head Self-Attention + RoPE（~60 行）
_FeedForward                FFN 两层 MLP（~10 行）
_DecoderBlock               Pre-LN decoder block（~30 行）
_CNNFrontend                多尺度时间卷积 + 通道混合 + 降采样（~50 行）
_EEGTransformer             Linear 投影 + Decoder 堆叠 + 分类头（~50 行）
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
| `bci/decoder/transformer.py` | ~220 | 核心实现（RoPE + Causal MHA + GPT 风格头） |
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
| **单元：RoPE** | 不同位置的旋转角度、Q·K 相对位置编码正确性 |
| **单元：Causal Mask** | 上三角 -inf 屏蔽、位置 i 只能看 ≤ i |
| **单元：Causal MHA** | 形状一致性、causal mask 应用、RoPE 集成 |
| **单元：DecoderBlock** | Pre-LN、Residual、维度保持 |
| **单元：CNN 前端** | 多尺度输出拼接、降采样形状 |
| **单元：EEGTransformer** | 逐位置线性头、最后位置切片 |
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
