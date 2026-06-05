# Transformer 解码器 — 设计稿

**日期**：2026-06-03
**状态**：待审阅
**目标**：在 BCI 解码框架中新增 `Transformer` 解码器，作为可拔插插件。

> **命名说明**：本文中"Transformer 解码器"（Transformer decoder）指 GPT 风格的因果自回归式架构（causal MHA + 末位切片），**不是** encoder-decoder 架构（无 cross-attention、无编码器）。命名沿用 BCI 领域惯用说法（"decoder"=分类器），与原始 Transformer 论文术语不同。

## 背景与目标

项目当前有 4 个解码器：`lda` / `ssvep` / `fbcca` / `cnn`，通过 `@register` 装饰器注册到 `bci/decoder/__init__.py` 的注册表。新增 Transformer 解码器，沿用现有 ABC 接口（`fit` / `predict` / `predict_proba` / `save` / `load`）。

**核心要求**：
- 遵循可拔插、模块化、接口标准化的设计原则
- 与现有 `CNNDecoder` 共享 PyTorch 可选依赖
- 保持零新增第三方依赖
- 与 LDA / CNN / SSVEP / FBCCA 共享同一种接口契约（只看 `(n_channels, n_times)` 形状输入）
- **Sliding window 实时流式不在 decoder 责任范围内**——由应用层管理 buffer、触发节奏、trial 边界

## 设计决策

| 维度 | 决策 | 理由 |
|------|------|------|
| 架构 | **轻量 Token Embedding（Conv1d）+ GPT 风格 Transformer** | attention 太长会浪费计算，需要 token 化 |
| Token Embedding | `Conv1d(n_ch, n_ch, kernel=20, stride=10)` | 50% 重叠，纯时间降采样 + 局部平滑 |
| 位置编码 | **RoPE**（旋转位置编码） | 在 MHA 内部编码，相对位置自然、长度可外推 |
| 注意力 | **单向因果**（causal mask） | 末位切片下与双向精度几乎等价；为未来 KV cache 留口 |
| 分类方式 | **无 CLS，逐位置分类头，取最后位置** | 因果 mask 下末位 = 全窗口聚合 |
| 输入投影 | `Linear(n_ch, d_model)` | 显式对齐到 d_model |
| 模型长度 | **length-agnostic** | 架构支持任意 `X.shape[2] >= kernel`（见"length-agnostic 设计"） |
| n_channels 传入 | **从 X.shape[1] 在 fit 时推断、锁存** | 上游 `decode(epochs_data, ...)` 隐式携带 |
| n_times 锁存 | **不锁存**（仅限推理） | 模型 length-agnostic，**推理时** n_times 任意（>= kernel）；**训练时** v1 要求同形 |
| 实时 streaming | **不实现** | 由应用层 SlidingWindow wrapper 负责（见末尾章节） |
| KV cache | **不实现**（后续扩展） | 当前 sliding window 抽象下不需要 |
| 依赖 | 手写多头自注意力 + RoPE | 零新依赖 |
| 注册方式 | `@register('transformer')` | 沿用现有 ABC 模式 |
| 保存格式 | `torch.save/load` | 与 `CNNDecoder` 一致 |

**核心设计**：用单层 Conv1d 把 `n_times` 个 time-domain sample 降采样为 `n_tokens = (n_times - kernel) / stride + 1` 个 token，作为 Transformer 输入序列。注意力专注于 token 间的时序关系。**因果 mask + 取最后位置**使得窗口末端是"基于整个窗口的预测点"。

**接口契约（与 LDA / CNN / SSVEP / FBCCA 完全一致）**：

```python
decoder.fit(X, y)               # X: (n_samples, n_ch, n_times) — fit 时锁 n_channels
decoder.predict(X)              # X: (B, n_ch, n_times) — 返回 (B,) 类别
decoder.predict_proba(X)        # X: (B, n_ch, n_times) — 返回 (B, n_classes) 概率
decoder.save(path) / load(path) # 持久化
```

## 架构

### 核心抽象：length-agnostic + 应用层管 sliding window

**两件事分开**：
- **Decoder**：只看 `(n_ch, n_times)` 形状的输入，输出 `(n_classes,)` 概率。**与 LDA / CNN / SSVEP / FBCCA 一致**。
- **应用层（SlidingWindow wrapper）**：维护 sample 缓冲、按节奏取出窗口、调 `predict_proba`。**任何 decoder 都能用同一个 wrapper**。

**为什么 decoder 不持有 sliding window**：
- LDA / CNN / SSVEP / FBCCA 都不持有，Transformer 没有理由特化
- streaming 逻辑（buffer / 触发 / trial 边界）应在应用层，业务相关
- decoder 状态越多，越难测试、越难复用

### Length-agnostic 设计

**Transformer 架构是 length-agnostic 的**：

| 组件 | 是否依赖序列长度 |
|------|----------------|
| `Conv1d(n_ch, n_ch, k, s)` | ❌ 处理任意输入长度 |
| `Linear(n_ch, d_model)` | ❌ 逐 token 映射 |
| DecoderBlock (MHA + FFN) | ❌ 全 token-wise |
| RoPE | ⚠️ 位置是整数，可处理任意长度；**训练外的位置有外推风险** |
| 末位切片 | ❌ 永远是最后那个 token |
| 分类头 | ❌ 逐 token 映射 |

**实际约束**：
- `X.shape[2] >= kernel`（必须能形成至少 1 个 token）
- `X.shape[1] == self.n_channels`（模型架构固定，n_channels 锁存在 fit 时）
- 其他任意 `n_times` 都接受

**训练/推理 size 关系**：

| 场景 | 是否工作 | 备注 |
|------|---------|------|
| 推理 size = 训练 size | ✅ 最优 | 设计与训练分布完全一致 |
| 推理 size < 训练 size | ✅ OK | 位置在训练分布内，末位仍有意义 |
| 推理 size > 训练 size | ⚠️ RoPE 外推 | 模型架构 OK，位置编码超出训练范围，**质量可能下降** |
| 推理 size ≪ 训练 size（1-2 token） | ⚠️ 退化 | 末位 token 上下文极少 |

**实践建议**：
- 默认：训练 size = 推理 size
- 不在 v1 引入自动 size 适配或外推缓解

### 数据流

```
输入: (B, n_channels, n_times)   ←  训练数据 / 批量推理 / 应用层 wrapper 取出的窗口
                                    n_times 可变，只要 >= kernel
   ↓
[Token Embedding 层]  ← 纯时间降采样，不改通道数
  Conv1d(n_channels, n_channels, kernel=20, stride=10, padding=0): (B, n_channels, n_tokens)
        n_tokens = floor((n_times - 20) / 10) + 1
        例: n_times=1000 → n_tokens=99；n_times=500 → n_tokens=49；n_times=20 → n_tokens=1
   ↓
Permute → (B, n_tokens, n_channels)
   ↓
[输入投影] Linear(n_channels → d_model)
   ↓
[N × Decoder Blocks（带 RoPE + Causal Mask）]
   每个 block 保持形状：(B, n_tokens, d_model) → (B, n_tokens, d_model)
   RoPE 位置 = 0..n_tokens-1（基于当前 n_tokens，每次调用都重置）
   ↓
逐位置 Linear(d_model → n_classes): (B, n_tokens, n_classes)
   ↓
取最后位置 [:, -1, :]: (B, n_classes)   ← 因果 mask 下末位 = 全窗口聚合
   ↓
softmax → (B, n_classes) 概率
```

### Token Embedding 设计

**为什么需要 Token Embedding**：
- 直接把 `n_times` 个 sample 喂 attention → `n_times²` ops/层 → 计算浪费
- 降为 `n_tokens ≈ n_times/10` → `n_tokens²` ops/层 → **~100 倍加速**
- 用单层 Conv1d 把 `n_times` 步 → `n_tokens` 个 token，**同时完成降采样 + 局部平滑**

**为什么用 kernel=20, stride=10**：
- 50% 重叠：每个时间步被 2 个相邻 token 共用 → 提供滑动上下文，无信息丢失
- n_tokens 足够细（每个 token = 10 时间步 ≈ 62.5ms @ 160Hz）
- 参数量适中：n_channels × n_channels × 20
- 边界不补 0：n_tokens = floor((n_times-20)/10)+1，**实际多少用多少，不 padding**

**为什么不无重叠（k=20, s=20）**：
- n_tokens 太粗（每个 token = 20 时间步 = 125ms）
- 时间分辨率不够细，错过 SSVEP 相位、MI 动态等特征
- 50% 重叠可让相邻 token 共享信息，避免边界割裂

**v1 已知限制：SSVEP 相位精度**
- k=20, s=10 下每个 token = 10 时间步 ≈ 62.5ms（@160Hz）
- SSVEP 典型频率 8–15Hz，对应周期 67–125ms
- 64Hz 以上的 SSVEP 高频谐波分量可能无法精确分辨
- v1 推荐 Transformer 用于 MI / ERP 任务；SSVEP 优先选 `ssvep` / `fbcca` 解码器
- 解决路径（不在 v1 范围）：减小 stride（如 s=4, k=8）或换用复数特征输入

**为什么不更大 kernel**：
- k=40, s=10：参数量翻倍，BCI 小样本易过拟合
- n_tokens 够用，不需要额外平滑

**为什么不对齐到固定数**：
- padding 会让首末 token 含 0，引入边界伪迹
- 模型对实际 token 数 vs 凑整不敏感
- 用实际长度，避免无意义的 padding

### Token Embedding 与 Patch 切分的关系

**Token Embedding = "patch 化"的实现方式**（以 n_times=1000 为例）：

| 方式 | 实现 | tokens | 重叠 | 参数量（n_ch=d_model=64） | 信息覆盖 |
|------|------|--------|------|--------|----------|
| Mean Pool | `F.avg_pool1d(10)` | 100 | 无 | 0 | 100% |
| **Conv1d(k=20, s=10)** ✅ | `Conv1d(64, 64, 20, 10)` | **99** | **50%** | **81,920** | **100%** |
| Conv1d(k=20, s=20) | `Conv1d(64, 64, 20, 20)` | 50 | 无 | 81,920 | 100% |
| Conv1d(k=10, s=10) | `Conv1d(64, 64, 10, 10)` | 100 | 无 | 40,960 | 100% |
| Conv1d(k=5, s=20) ❌ | `Conv1d(64, 64, 5, 20)` | 50 | 无 | 20,480 | 25% |

**关键约束**：
- kernel ≥ stride：无信息丢失
- kernel < stride：丢信息（k=5, s=20 丢 75%）
- 50% 重叠（k=2s）：相邻 token 共享信息，最常用

### Decoder Block 内部结构（Pre-LN + Causal MHA + RoPE）

```
输入: (B, n_tokens, d_model)   例: (B, 99, 64)
   ↓
[1] LayerNorm: (B, n_tokens, d_model)        ← Pre-LN
   ↓
[2] Causal Multi-Head Self-Attention with RoPE
   ├─ Q = Linear(d_model, d_model)(x)         # (B, n_tokens, d_model)
   ├─ K = Linear(d_model, d_model)(x)         # (B, n_tokens, d_model)
   ├─ V = Linear(d_model, d_model)(x)         # (B, n_tokens, d_model)
   ├─ Split into n_heads: (B, n_heads, n_tokens, head_dim)
   │   head_dim = d_model / n_heads  （d_model=64, n_heads=4 → head_dim=16）
   ├─ RoPE: rotate Q, K by position
   │   Q' = RoPE(Q, pos=0..n_tokens-1)
   │   K' = RoPE(K, pos=0..n_tokens-1)
   ├─ Causal Mask: 上三角置 -inf
   │   mask_qk[q, k] = -inf if k > q
   ├─ Attention = softmax(Q'K'^T / sqrt(head_dim) + mask)   # (B, n_heads, n_tokens, n_tokens)
   ├─ Dropout（attn dropout）
   ├─ Concat heads: (B, n_tokens, d_model)
   └─ Output projection: Linear(d_model, d_model)            # (B, n_tokens, d_model)
   ↓
[3] 残差连接: x + attn_out
   形状: (B, n_tokens, d_model)
   ↓
[4] LayerNorm: (B, n_tokens, d_model)        ← Pre-LN
   ↓
[5] FFN（前馈网络）
   ├─ Linear(d_model, 4×d_model)              # (B, n_tokens, 4×d_model)
   ├─ GELU
   ├─ Dropout
   └─ Linear(4×d_model, d_model)              # (B, n_tokens, d_model)
   ↓
[6] 残差连接: x + ffn_out
   形状: (B, n_tokens, d_model)
   ↓
Block 输出: (B, n_tokens, d_model)  ← 输入输出形状相同
```

**Dropout 位置（明确）**：
- MHA output projection **之后**、residual 之前
- FFN 第一个 Linear **之后**（GELU 之前或之后都可以）
- Pre-LN 风格**不**对 residual stream 加 dropout

### Causal Mask 详解

**约定**：`mask_qk[query, key]`，mask 为 -inf 表示该 (query, key) 对被屏蔽。
- `mask_qk[q, k] = 0` 表示 query=q 可以 attend 到 key=k
- `mask_qk[q, k] = -inf` 表示 query=q **不能** attend 到 key=k

**因果 mask**：位置 q 只能看 ≤ q 的 key，即
```
mask_qk[q, k] = 0   if k <= q
mask_qk[q, k] = -inf if k > q
```

**可视化**（n_tokens=5 例子，列=key，行=query）：

```
        key=0  key=1  key=2  key=3  key=4
query=0   0    -inf   -inf   -inf   -inf     ← 位置 0 只能看自己
query=1   0      0    -inf   -inf   -inf     ← 位置 1 能看 0,1
query=2   0      0      0    -inf   -inf
query=3   0      0      0      0    -inf
query=4   0      0      0      0      0       ← 位置 4 能看全部
```

**为什么用因果 mask**：
- **末位切片足够**：因果 mask 下，末位 token（位置 `n_tokens-1`）能 attend 到全部 0..n_tokens-1，**信息总量**与双向注意力相同
- **未来 KV cache 兼容**：若日后加 streaming prefix 推理，因果 mask 是 KV cache 的前提
- **训练目标对齐**：自回归式预训练（未来扩展）的天然选择

**与双向注意力的取舍**：

| 维度 | 双向 + [CLS] | 因果 + 末位切片（本设计） |
|------|-------------|----------------|
| 末位可见信息总量 | 全部 | 全部 |
| 聚合路径 | 一次 attention 直达 | 多层逐步汇聚 |
| 分类精度 | 基线 | 通常差距 < 1~2%，有时持平或反超 |
| 未来 KV cache 兼容性 | 需重新设计 | ✅ 天然兼容 |

**关键澄清**：
- 分类任务里，**信息总量**与双向等价；区别只在传播路径
- 真正的"表示能力损失"只出现在生成任务（必须预测下一 token）
- 一些 BCI/EEG 任务上**因果可能反超双向**（归纳偏置更贴合 EEG 局部时序结构）

**结论**：
- 因果 mask 是为分类任务精心选的，等价精度、留 KV cache 余量
- 若将来精度不够，可加 `predict_bidirectional` 入口；当前不预先实现

### RoPE 旋转位置编码

**为什么用 RoPE**：
- 通过 Q·K 点积自然编码相对位置（`Q·R(m-n)·K` 形式）
- 不增加参数量
- 训练位置范围 `[0, n_tokens_train)`，推理时 RoPE 自动适配窗口内的位置

**本设计中的位置语义**：
- 训练和推理都用**窗口内相对位置**：`positions = 0, 1, ..., n_tokens-1`
- 每次 `predict_proba` 调用都从位置 0 开始（因为窗口边界即位置边界）
- **位置范围不是固定的**——`n_tokens` 随 `X.shape[2]` 变
- 当 `n_tokens > n_tokens_train`（推理时 n_times 大于训练）时，RoPE 进入**外推区**（位置编码超出训练分布）

**简化实现**（d=2 例子）：
```
位置 0: 角度 = 0,    R = [[1, 0], [0, 1]]     # 单位旋转
位置 1: 角度 = θ,    R = [[cosθ, -sinθ], [sinθ, cosθ]]
位置 2: 角度 = 2θ,   R = [[cos2θ, -sin2θ], [sin2θ, cos2θ]]
...
```

**d_model=64 实现**：将 d_model 维分成 d_model/2 = 32 对，每对旋转不同角度（频率数为 d/2，不是 head_dim）：
```
θ_i = 1 / (10000^(2i/d_model))  for i ∈ [0, d_model/2) = [0, 32)
位置 m 的旋转角: m * θ_i
```
注：每个 head 独立应用 RoPE，但频率基数只与 d_model 有关，与 n_heads 无关。

### 分类头（窗口末位切片）

```
Transformer 输出: (B, n_tokens, d_model)   ←  n_tokens 由 n_times 决定（length-agnostic）
   ↓
逐位置 Linear(d_model → n_classes)
   每个位置独立映射：(B, n_tokens, d_model) → (B, n_tokens, n_classes)
   ↓
取最后位置 [:, -1, :]
   (B, n_tokens, n_classes) → (B, n_classes)
   ↓
CrossEntropyLoss(y, logits)
```

**为什么取最后位置**：
- 因果 mask 下，位置 `n_tokens-1` 能看到全部 0..n_tokens-1 的信息
- 最后位置的输出 = "基于整个窗口的预测"
- 训练和推理都用同一规则，**与 batch 推理完全一致**

### 模块拆分

```
bci/decoder/transformer.py  (~180 行)

_TokenEmbedding             Conv1d(n_ch, n_ch, k=20, s=10) 时间降采样（~15 行）
_InputProjection            Linear(n_ch → d_model) 通道对齐（~5 行）
_RotaryPositionalEmbedding  RoPE 旋转编码（~30 行）
_CausalMask                 因果 mask 生成（~10 行）
_CausalMHA                  Causal MHA + RoPE + dropout（~60 行）
_FeedForward                FFN 两层 MLP + dropout（~12 行）
_DecoderBlock               Pre-LN decoder block（~30 行）
_EEGTransformer             Decoder 堆叠 + 分类头（~50 行）
TransformerDecoder          Decoder ABC 包装 + save/load（~110 行）
```

**关键不变量**：
- 模型架构**与 LDA / CNN / SSVEP / FBCCA 同形**——`fit` / `predict` / `predict_proba` 即可
- **没有** `_RingBuffer` / `step()` / `reset_streaming()`——streaming 在应用层
- **没有** `window_size` / `decision_interval` 参数——length-agnostic，触发节奏应用层管

## 接口设计

### `TransformerDecoder` 公共 API

```python
class TransformerDecoder(Decoder):
    def __init__(
        self,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 3,
        kernel: int = 20,
        stride: int = 10,
        dropout: float = 0.2,
        epochs: int = 50,
        lr: float = 5e-4,
        weight_decay: float = 1e-4,
        device: str = 'cpu',
    ) -> None:
        # 构造时校验（早失败）
        assert d_model % n_heads == 0, f"d_model={d_model} must be divisible by n_heads={n_heads}"
        assert kernel >= stride, f"kernel={kernel} must be >= stride={stride} (no info loss)"
        assert kernel > 0 and stride > 0
        # n_channels 在 fit 时从 X.shape[1] 推断
        # n_times 推理时不锁存（length-agnostic）；训练时 v1 要求同形
        ...

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'TransformerDecoder':
        """训练。X: (n_samples, n_channels, n_times)，**v1 要求 batch 内 n_times 相同**。
        y: (n_samples,) 类别标签
        - 推断 n_channels = X.shape[1] → 锁存 self.n_channels
        - 推断 n_classes = len(np.unique(y)) → 锁存 self.classes_
        - 记录训练时的 n_tokens → self._train_n_tokens（推理时用于外推警告）
        - 第一次见到数据时构建模型（懒构建）
        - 全 batch 训练（AdamW + CrossEntropy）
        - 完成后 model.eval()
        """
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        """分类预测。X: (B, n_channels, n_times)。
        返回 (B,) 的 self.classes_[idx] 类别标签。
        """
        probs = self.predict_proba(X)
        idx = np.argmax(probs, axis=-1)
        return self.classes_[idx]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """概率预测。X: (B, n_channels, n_times)，n_times >= kernel（不锁存为训练 size）。
        返回 (B, n_classes) 概率。
        """
        ...

    def save(self, path: str | Path) -> None:
        """torch.save state_dict + 配置（参考 CNNDecoder）"""
        ...

    @classmethod
    def load(cls, path: str | Path) -> 'TransformerDecoder':
        """返回 decoder，模型结构与训练时一致"""
        ...
```

**`predict_proba` 内部流程**：

```python
def predict_proba(self, X):
    if not self._is_fitted():
        raise RuntimeError("Must call fit() before predict_proba()")
    if X.shape[1] != self.n_channels:
        raise ValueError(f"n_channels mismatch: expected {self.n_channels}, got {X.shape[1]}")
    if X.shape[2] < self.kernel:
        raise ValueError(
            f"X.shape[2]={X.shape[2]} < kernel={self.kernel}; "
            f"need at least 1 token"
        )
    n_tokens = (X.shape[2] - self.kernel) // self.stride + 1
    if n_tokens > self._train_n_tokens:
        # 训练分布外，RoPE 外推
        import warnings
        warnings.warn(
            f"n_tokens={n_tokens} > train n_tokens={self._train_n_tokens}; "
            f"RoPE position extrapolation; accuracy may degrade",
            stacklevel=2,
        )
    Xt = torch.tensor(X, dtype=torch.float32, device=self.device)
    self.model.eval()
    with torch.no_grad():
        logits = self.model(Xt)  # (B, n_classes) 末位 token
    return torch.softmax(logits, dim=-1).cpu().numpy()
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

if TORCH_OK:

    class _EEGTransformer(nn.Module):
        ...

    class TransformerDecoder(Decoder):
        ...
```

未安装 PyTorch 时 `TransformerDecoder` 类不定义（`bci.decoder.transformer` 模块导入不报错），注册表的 `_TransformerDecoder.create()` 在调用时才尝试 `from bci.decoder.transformer import TransformerDecoder`——与 `CNNDecoder` 完全一致。

### n_channels 处理（fit 时从 X.shape 推断）

```python
def fit(self, X, y):
    n_samples, n_channels, n_times = X.shape
    # 推断并锁存 n_channels（模型架构需要）
    self.n_channels = n_channels
    # 记录训练时的 n_tokens（仅用于外推警告，RoPE 位置在 token 空间）
    self._train_n_tokens = (n_times - self.kernel) // self.stride + 1
    # 推断 n_classes
    classes, y_idx = np.unique(y, return_inverse=True)
    self.classes_ = classes
    self._n_classes = len(classes)
    # 懒构建模型
    self._build_model()
    # 训练（full-batch, AdamW, CrossEntropy）
    self.model.train()
    opt = optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
    criterion = nn.CrossEntropyLoss()
    Xt = torch.tensor(X, dtype=torch.float32, device=self.device)
    yt = torch.tensor(y_idx, dtype=torch.long, device=self.device)
    for _ in range(self.epochs):
        opt.zero_grad()
        logits = self.model(Xt)  # (n_samples, n_classes)
        loss = criterion(logits, yt)
        loss.backward()
        opt.step()
    self.model.eval()
    return self
```

**`n_channels` 由上游流程传递**：调用方只需 `decode(epochs_data, labels, method='transformer')`，无需在 GUI/CLI 显式指定通道数。`epochs_data.shape[1]` 携带 n_channels 信息，fit 时自动识别。

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

**无需新增 GUI 控件**：`n_channels` 由上游 `epochs_data.shape[1]` 携带，Transformer decoder 在 fit 时自动识别。

## 超参数

| 参数 | 默认值 | 范围 | 备注 |
|------|--------|------|------|
| `d_model` | 64 | [32, 128] | 嵌入维度；需被 `n_heads` 整除 |
| `n_heads` | 4 | [1, 8] | head_dim = d_model / n_heads |
| `n_layers` | 3 | [1, 6] | 防止过拟合 |
| `kernel` | 20 | [5, 50] | Token Embedding 卷积核 |
| `stride` | 10 | [1, kernel] | Token Embedding 步长（kernel ≥ stride 无信息丢失） |
| `dropout` | 0.2 | [0.0, 0.5] | |
| `epochs` | 50 | [10, 200] | 训练轮数 |
| `lr` | 5e-4 | [1e-5, 1e-2] | |
| `weight_decay` | 1e-4 | [0.0, 1e-2] | AdamW |

**`n_channels` 不在超参数表中**：从 `X.shape[1]` 在 fit 时自动推断并锁存。

**没有 `window_size` / `decision_interval` 参数**：
- 模型 length-agnostic，n_times 任意（>= kernel）
- streaming 触发节奏由应用层决定

## 文件清单

### 新增

| 文件 | 行数 | 用途 |
|------|------|------|
| `bci/decoder/transformer.py` | ~180 | 核心实现（Token Embedding + RoPE + Causal MHA） |
| `bci/tests/test_transformer.py` | ~150 | 单元测试 |
| `bci/tests/test_transformer_e2e.py` | ~80 | 集成测试（save/load + decode + length-agnostic） |

### 修改

| 文件 | 改动 |
|------|------|
| `bci/decoder/__init__.py` | 追加 `@register('transformer')`（~10 行） |
| `bci/gui/widgets/decode_page.py` | `addItems` 列表加 `'transformer'`（1 行） |

## 测试策略

| 类型 | 内容 |
|------|------|
| **单元：RoPE** | 不同位置的旋转角度、Q·K 相对位置编码正确性 |
| **单元：Causal Mask** | 上三角 -inf 屏蔽、`mask_qk[q, k] = -inf if k > q` |
| **单元：Causal MHA** | 形状一致性、causal mask 应用、RoPE 集成、dropout 位置 |
| **单元：DecoderBlock** | Pre-LN、Residual、维度保持、dropout 行为 |
| **单元：Token Embedding** | Conv1d(k=20,s=10) 输出长度公式正确（n_times 可变） |
| **单元：EEGTransformer** | 逐位置线性头、最后位置切片、length-agnostic 形状 |
| **单元：边界** | n_channels 不匹配、n_times<kernel、n_heads 不整除、kernel<stride |
| **单元：length-agnostic** | 同一模型能处理 n_times=20 / 100 / 1000 / 2000 |
| **集成：save/load** | 往返预测一致性 |
| **集成：decode()** | 跑通 `decode(method='transformer')` 端到端流程 |
| **集成：与 LDA/CNN 一致性** | `predict_proba` 接口签名相同、返回形状相同 |

## 训练细节

- **优化器**：AdamW
- **Loss**：CrossEntropyLoss
- **批大小**：full-batch（BCI 数据量小）
- **n_times 约束**：v1 **要求同形**——训练 batch 内所有 sample 的 `n_times` 必须相同。架构本身 length-agnostic，但训练循环用 `torch.tensor(X, ...)` + 批处理 forward，不支持混合长度
- **推理 n_times**：任意（>= kernel），与训练 size 不同不报错，只触发外推警告
- **典型场景**：训练和推理用同一 n_times
- **数据增强**：不在初版中实现
- **学习率调度**：不在初版中实现
- **早停**：不在初版中实现
- **不使用 random prefix truncation**：模型在训练和推理都见完整窗口，不需要 prefix 鲁棒性

## 边界处理

| 情况 | 处理 |
|------|------|
| `d_model % n_heads != 0` | `__init__` 抛 `ValueError`（构造时早失败） |
| `kernel < stride` | `__init__` 抛 `ValueError`（避免信息丢失） |
| `kernel <= 0` 或 `stride <= 0` | `__init__` 抛 `ValueError` |
| 训练 `X.shape[0] != len(y)` | `fit()` 抛 `ValueError` |
| `predict_proba` 时 `X.shape[1] != n_channels` | `ValueError`（fit 锁定） |
| `predict_proba` 时 `X.shape[2] < kernel` | `ValueError`（无法形成 1 个 token） |
| `predict_proba` 时 `n_tokens > train n_tokens` | **允许**，warn 一次（RoPE 外推区；按 token 数判，不用 sample 数） |
| `predict_proba` / `predict` 前未 `fit()` | `RuntimeError` |
| `n_classes < 2` | `fit()` 抛 `ValueError` |
| PyTorch 未安装 | `TransformerDecoder` 类不定义；调用 `create()` 时 `ImportError`（与 CNN 一致） |

## 风险与权衡

| 风险 | 缓解 |
|------|------|
| BCI 小样本易过拟合 | dropout=0.2、n_layers=3、强正则 |
| Transformer 训练不稳定 | Pre-LN、lr=5e-4、AdamW |
| 推理 n_times > 训练 n_times | 允许但 warn；位置编码进入外推区，质量可能下降 |
| 推理 n_times ≪ 训练 n_times（1-2 token） | 末位 token 上下文不足，预测基本靠训练先验；用户责任 |
| 参数量 | Token Embedding ~82K（n_ch=d_model=64, k=20） + 3 × DecoderBlock ~150K ≈ **230K**（d_model=64, n_heads=4）；可通过降 `d_model` 或 `n_layers` 压缩 |
| **推理**时不同 trial n_times 不一致 | model 自动适配（length-agnostic）；仅当 n_tokens > 训练时触发外推警告。**训练时** n_times 必须同形（见"训练细节"） |

## 后续扩展（不在本次实现范围）

- **KV cache**（仅当未来放弃 sliding window、回到 growing prefix 时再考虑；sliding window 下位置变导致 cache 失效）
- **Length-bucketed training**（按 `n_times` 分桶训练，每桶内同形，跨桶混 batch）
  - 动机：当前 v1 限制同形 n_times；分桶可支持混合长度 trial
  - 实现：custom `Dataset` + 按长度分桶的 `Sampler` + `collate_fn`（仅 stack，不 padding）
  - 关键风险：RoPE 位置频率跨桶不均（短桶位置 0..k 反复训练，长桶位置仅偶尔曝光）→ 长位置编码欠拟合
  - 待定超参：桶数 / 划分策略（quantile vs fixed-width）/ 桶内 batch size / 排序
  - 前置：v1 上线、有真实混合长度数据后再评估收益
- **基准对比 vs CNNDecoder**（同一公开数据集的精度 + 推理速度对比，需先选定数据集与评测脚本）
- **数据增强**（时间抖动、通道掩码）
- **跨被试预训练**
- **注意力权重可视化**
- **与 `CNNDecoder` 模型蒸馏**
- **学习率调度 + 早停**
- **RoPE 外推优化**（如 NTK-aware scaling、动态 θ 基数）
- **双向 attention 入口**（`predict_bidirectional`）

## 应用层 SlidingWindow 模式（参考）

> Decoder 不持有 streaming 状态。Sliding window 逻辑由应用层实现，可被任何 decoder 复用。

### 职责划分

| 层 | 职责 |
|----|------|
| 采集层 | 原始 sample 流（LSL / BrainFlow / 文件读取） |
| **应用层 SlidingWindow** | 维护 sample buffer、按节奏取窗口、调 decoder |
| **Decoder** | 看到窗口，输出概率，不关心窗口来源 |
| 应用控制 | 拿概率做反馈 / 控制 / 记录 |

### 参考实现（应用层，与 decoder 解耦）

```python
import numpy as np
from collections import deque
from typing import Optional

class SlidingWindow:
    """任意 decoder 都能复用的 streaming wrapper。

    使用方式：
        sw = SlidingWindow(n_channels=64, window_size=1000, decision_interval=25)
        decoder = create_decoder(method='transformer')  # 或 'lda' / 'cnn' / 'ssvep' / 'fbcca'
        decoder.fit(X_train, y_train)
        for chunk in eeg_stream:
            sw.push(chunk)
            if sw.ready():
                window = sw.get_window()                # (n_ch, window_size)
                probs = decoder.predict_proba(window[None])[0]  # (n_classes,)
                act(probs)
    """

    def __init__(self, n_channels: int, window_size: int, decision_interval: int):
        assert decision_interval > 0
        assert decision_interval <= window_size
        self.n_channels = n_channels
        self.window_size = window_size
        self.decision_interval = decision_interval
        self._buf = np.zeros((n_channels, window_size), dtype=np.float32)
        self._n_filled = 0
        self._write_pos = 0
        self._since_last = 0

    def push(self, chunk: np.ndarray) -> None:
        """chunk: (n_channels, n_new_samples)"""
        if chunk.shape[0] != self.n_channels:
            raise ValueError(...)
        for i in range(chunk.shape[-1]):
            self._buf[:, self._write_pos] = chunk[:, i]
            self._write_pos = (self._write_pos + 1) % self.window_size
        self._n_filled = min(self._n_filled + chunk.shape[-1], self.window_size)
        self._since_last += chunk.shape[-1]

    def ready(self) -> bool:
        return (
            self._n_filled >= self.window_size      # 还没填满就不能预测
            and self._since_last >= self.decision_interval
        )

    def get_window(self) -> np.ndarray:
        """返回 (n_channels, window_size)，按时间顺序"""
        if self._n_filled < self.window_size:
            return self._buf[:, :self._n_filled]
        return np.concatenate(
            [self._buf[:, self._write_pos:], self._buf[:, :self._write_pos]],
            axis=-1,
        )

    def consume(self) -> None:
        """调用方取走窗口后调用，重置 since_last"""
        self._since_last = 0

    def reset(self) -> None:
        """清空（新 trial / session）"""
        self._buf[:] = 0
        self._n_filled = 0
        self._write_pos = 0
        self._since_last = 0
```

**关键点**：
- `SlidingWindow` 不属于任何 decoder，可放在 `bci/streaming/sliding_window.py`（v1 不实现，仅 spec 描述）
- 调用方决定 trial 边界（调 `reset()`）
- `window_size` / `decision_interval` 是 streaming 配置，与 decoder 解耦
- 同一 `SlidingWindow` 可换不同 decoder（transformer / LDA / CNN 都行）

## 设计原则遵守

- **单一职责**：每个模块一个清晰目的；streaming 不在 decoder 责任内
- **接口隔离**：`Decoder` ABC 统一接口（fit/predict/predict_proba/save/load），**不加新方法**
- **依赖倒置**：高层（`decode()`）不依赖具体实现；`n_channels` 由 `epochs_data.shape[1]` 隐式传递
- **开闭原则**：新增解码器无需修改现有代码（除了注册表 + GUI 下拉框）
- **不冗余**：`n_channels` 不出现在 `__init__` 签名里，避免和 `X.shape` 双重来源
- **与现有 decoder 一致**：接口签名、输入输出形状、save/load 流程与 LDA / CNN / SSVEP / FBCCA 完全一致
- **length-agnostic**：模型对 n_times 不敏感（除最小约束和 RoPE 外推警告）
- **职责分离**：streaming 在应用层，模型在 decoder 层，互不耦合
