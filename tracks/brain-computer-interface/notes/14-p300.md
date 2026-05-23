# Week 5 Day 14：P300 事件相关电位

## 1. P300 是什么？

**P300** 是一种事件相关电位（ERP）成分，在**罕见、与任务相关的刺激**出现后约 300ms，在头顶**Pz（顶叶中线）**处记录到的一个正向波。

### 关键参数

| 参数 | 典型值 |
|------|--------|
| 峰值潜伏期 | 250-400 ms |
| 头皮分布 | Pz 最大（顶叶中线） |
| 振幅 | 2-10 μV |
| 触发条件 | Oddball 范式（罕见 + 任务相关） |

---

## 2. Oddball 范式

P300 的产生需要两个条件：

1. **稀有性**：目标刺激出现概率低（通常 P < 0.3）
2. **任务相关性**：被试必须对目标做反应（计数、按键等）

```
刺激序列：  标  标  标  ★  标  标  ★  标  标  标  ...
                      ↑              ↑
                   目标(rare)     目标(rare)

概率：      80% 标准（standard），20% 目标（target）
任务：      "数一下目标出现了几次"
```

- 目标概率越低 → P300 振幅越大
- 注意力越集中 → P300 振幅越大

---

## 3. P300 Speller（Farwell-Donchin 拼写器）

### 3.1 工作原理

```
6×6 字符矩阵：
  A B C D E F
  G H I J K L      ← 目标字符 H
  M N O P Q R
  S T U V W X
  Y Z 1 2 3 4
  5 6 7 8 9 0

闪烁序列：逐行逐列随机闪烁
  Row 0: A-F  →  非目标（H不在这一行）
  Row 1: G-L  →  目标！（H在这一行）→ 诱发 P300
  Col 0: A,G,M,S,Y,5  →  非目标
  Col 1: B,H,N,T,Z,6  →  目标！→ 诱发 P300
```

- 只有包含目标字符的行/列闪烁才诱发 P300
- 检测哪一行 + 哪一列诱发了 P300 → 确定字符

### 3.2 时序参数

| 参数 | 典型值 |
|------|--------|
| 闪烁持续时间 | 100-125 ms |
| 刺激间隔（ISI） | 50-75 ms |
| 每次重复的闪烁数 | 12（6行 + 6列） |
| 重复次数 | 10-15 次 |
| 单字符选择时间 | ~20-36 s |

---

## 4. P300 检测方法

### 4.1 信号平均

单次试验的 P300 埋没在噪声中（SNR ≈ 0.1），需要多次平均：

$$\text{SNR}_{avg} = \text{SNR}_{single} \times \sqrt{N}$$

- $N$ = 重复次数
- 10 次平均 → SNR 提高 ~3.2 倍
- 15 次平均 → SNR 提高 ~3.9 倍

### 4.2 特征提取

常用时间窗口振幅作为特征：

| 窗口 | 时间范围 | 对应成分 |
|------|---------|---------|
| N1 | 100-150 ms | 早期负波 |
| P2 | 150-250 ms | 早期正波 |
| P3a | 250-350 ms | 额叶 P300 |
| **P3b** | **300-400 ms** | **顶叶 P300（最关键）** |
| SW | 400-550 ms | 慢波 |

### 4.3 Stepwise LDA

P300 分类最常用的分类器：

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

# 二分类：target flash vs non-target flash
clf = LinearDiscriminantAnalysis()
clf.fit(X_features, y_labels)  # y: 1=target, 0=non-target

# 对每一行/列的闪烁打分
scores = clf.decision_function(X_test)

# 累积多轮重复的分数
# 得分最高的行 + 得分最高的列 → 确定字符
```

为什么用 LDA 而不是深度学习？
- 训练数据少（每次校准只有几十分钟）
- 特征维度低（时间窗口振幅，5-20 维）
- 实时性要求高（每次闪烁后 200ms 内出结果）

---

## 5. P300 vs 其他 BCI 范式

| 范式 | 准确率 | ITR (bits/min) | 训练量 | 舒适度 | 应用场景 |
|------|--------|---------------|--------|--------|---------|
| **P300** | ~90% | 20-30 | 几乎不需 | 中（需盯屏） | 拼写器 |
| **SSVEP** | ~92% | 50-60 | 不需 | 低（视觉疲劳） | 高速选择 |
| **MI** | ~80% | 10-20 | 大（需训练） | 高 | 康复训练 |
| **SCP** | ~75% | 5-10 | 中等 | 高 | 慢速控制 |

### P300 的核心优势

1. **几乎不需要训练**：健康被试第一次就能用
2. **准确率高**：90%+ 比较容易达到
3. **35+ 目标选择**：6×6 矩阵提供 36 个选项

### P300 的核心劣势

1. **ITR 低**：需要多次重复，单字符 ~20-30s
2. **需要视觉注视**：严重运动障碍者可能无法注视
3. **疲劳**：长时间使用导致 P300 振幅下降
4. **依赖显示器**：必须有视觉刺激设备

---

## 6. 数学补充

### ITR 计算

$$\text{ITR} = \frac{60}{T} \left[ \log_2 N + P \log_2 P + (1-P) \log_2 \frac{1-P}{N-1} \right]$$

- $T$：单次选择时间（秒）
- $N$：目标数量
- $P$：准确率

P300 Speller 示例（N=36, P=0.90, T=25s）：
$$\text{ITR} = \frac{60}{25} \times [\log_2 36 + 0.9 \times \log_2 0.9 + 0.1 \times \log_2 \frac{0.1}{35}]$$
$$\approx 2.4 \times [5.17 - 0.137 - 0.534] \approx 10.8 \text{ bits/min}$$

---

## 7. 本章小结

| 步骤 | 方法 | 要点 |
|------|------|------|
| 范式 | Oddball | 稀有 + 任务相关 → P300 |
| 采集 | EEG (Pz为中心) | 8-16 通道，250Hz |
| 预处理 | 带通 0.1-30Hz | 去除高频噪声和慢漂移 |
| 特征 | 时间窗口振幅 | P3b 窗口 (300-400ms) 最关键 |
| 分类 | Stepwise LDA | 重复累积 + 行列交叉定位 |
| 评估 | ITR / 准确率 / ROC | 准确率 vs 速度的 trade-off |

---

## 参考文献

- Farwell, L.A. & Donchin, E. (1988). Talking off the top of your head: toward a mental prosthesis utilizing event-related brain potentials. *Electroencephalography and Clinical Neurophysiology*, 70(6), 510-523.
- Krusienski, D.J. et al. (2006). A comparison of classification techniques for the P300 Speller. *Journal of Neural Engineering*, 3(4), 299.
- Lenhardt, A. et al. (2008). An improved P300-based brain-computer interface. *IEEE TNSRE*, 16(1), 50-56.
