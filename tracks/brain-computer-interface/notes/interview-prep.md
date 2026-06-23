# BCI 面试补强清单

> 基于岗位 JD 逆向分析，在已有 BCI 项目基础上，面试前 1-2 周需重点补强的知识点。

---

## 1. LSL（Lab Streaming Layer）协议

**为什么补**：BCI 实时数据采集的事实标准，几乎所有实验室设备都通过 LSL 推流。

**学习目标**：
- 理解 LSL 架构：Outlet（发送端）→ Network → Inlet（接收端）
- 能用 `pylsl` 写一个简单的 EEG 数据收发 demo
- 了解时间同步机制（clock synchronization）

**参考**：
- 官方文档：https://labstreaminglayer.readthedocs.io/
- `pylsl`：`pip install pylsl`
- MNE-LSL：https://mne.tools/mne-lsl/stable/（MNE 官方 LSL 适配）

**行动项**：
- [ ] 阅读 LSL 官方 tutorial
- [ ] 用 pylsl 写一个模拟 Outlet + Inlet 的 demo 脚本

---

## 2. EEG 国际 10-20 电极系统

**为什么补**：面试大概率问"常用的电极有哪些"、"C3/C4 在哪"，这是 EEG 基本功。

**学习目标**：
- 背下 10-20 系统核心电极：Fp1/Fp2、F3/F4、C3/C4、P3/P4、O1/O2、Fz/Cz/Pz/Oz
- 理解命名规则：字母=脑区（F=额、C=中央、P=顶、O=枕、T=颞），数字=左右（奇数左、偶数右、z 中线）
- 运动想象常用电极：C3/C4/Cz（对应运动皮层手区）
- SSVEP 常用电极：O1/O2/Oz（对应枕叶视觉区）

**行动项**：
- [ ] 默画 10-20 电极分布图
- [ ] 能口述 C3/C4/Oz 的解剖位置与对应脑功能

---

## 3. 常见伪迹来源

**为什么补**："去伪迹"是岗位核心要求，面试会问伪迹类型和去除方法。

| 伪迹类型 | 来源 | 频率特征 | 去除方法 |
|---------|------|---------|---------|
| 眼电（EOG） | 眨眼/眼球运动 | 低频 <4Hz，额区大 | ICA 分离 EOG 成分 |
| 肌电（EMG） | 面部/颈部肌肉 | 高频 >30Hz，宽带 | 带通滤波（<40Hz）+ ICA |
| 工频干扰 | 电力线 50Hz | 50Hz 尖峰 | Notch 滤波 |
| 电极接触不良 | 出汗/松动 | 缓慢漂移 | 坏导检测 + 插值 |
| 心电（ECG） | 心跳 | ~1Hz 周期性，QRS 复合波 | ICA 或 ECG 通道回归 |

**行动项**：
- [ ] 复习 MNE ICA 流程：`mne.preprocessing.ICA` → `find_bads_eog` → `apply`
- [ ] 准备口述：EOG 和 EMG 的区别与去除策略

---

## 4. CSP（Common Spatial Pattern）

**为什么补**：MI 解码经典算法，论文高频出现。你的 `bci/decoder/` 目前缺 CSP，补上可加分。

**学习目标**：
- 理解 CSP 原理：最大化一类方差同时最小化另一类方差
- 知道 CSP + LDA 是 MI-BCI 经典 pipeline
- 了解正则化 CSP（RCSP）和滤波器组 CSP（FBCSP）

**行动项**：
- [ ] 在 `bci/decoder/` 中实现 `CSPDecoder`（可用 `mne.decoding.CSP` 或 `sklearn` 手写）
- [ ] 在 PhysioNet MI 数据上跑 CSP + LDA，对比纯 LDA 效果

---

## 5. 常见 EEG 硬件设备

**为什么补**：面试可能问"你了解哪些采集设备"，体现行业认知。

| 设备 | 类型 | 通道数 | 接口 |
|------|------|--------|------|
| OpenBCI | 开源 DIY | 8-16ch | LSL / Bluetooth |
| g.tec | 科研级 | 16-64ch | LSL / SDK |
| Neuroscan | 临床/科研 | 32-256ch | .set 格式 |
| BrainProducts | 科研级 | 32-256ch | .vhdr 格式（BrainVision） |
| Neuracle（博睿康） | 国产 | 32-64ch | LSL / 自有 SDK |
| Emotiv | 消费级 | 14ch | SDK / LSL |

**关键点**：你的 `bci/loader/` 已支持 EDF / FIF / EEGLAB / BrainVision 四种格式，覆盖了 Neuroscan 和 BrainProducts 的数据，面试可以强调这一点。

**行动项**：
- [ ] 记住上述设备名称和数据格式对应关系

---

## 6. STAR 故事准备

面试中用 STAR 法则（Situation-Task-Action-Result）组织回答。

### 故事 1：Snakemake 自研框架

- **S**：生信分析流程使用 Snakemake，但 rule 语法是静态的，模块无法灵活组合
- **T**：需要一个可动态拼接的流程框架，降低分析人员组合模块的成本
- **A**：抛弃 rule DSL，直接调用 Snakemake 内部接口，通过代码动态生成 rule 单元，规范 IO 类型后模块可像积木拼接
- **R**：分析人员可自由组合模块，无需写 rule，流程开发效率显著提升

### 故事 2：BCI Pipeline 全链路设计

- **S**：自学 BCI 后需要将分散的信号处理/解码代码整合为可用工具
- **T**：设计一个从原始数据到解码结果的完整 Pipeline
- **A**：分层架构 — `source`（4 种 EEG 格式 reader）/`domain`（preprocessor + epocher + dataset + config 纯函数）/`application`（PipelineSession 编排 + MVP 控制层：BatchPresenter + IBatchView ABC + RunState 状态机）/`decoder`（6 种注册式解码器，懒加载）/`gui`（PyQt6 BatchTab）。dataclass + YAML 配置，`invalidate_from` 增量重执行。
- **R**：支持 4 种 EEG 格式、6 种解码器（LDA/SSVEP/FBCCA/CSP/CNN/Transformer-GPT+Transformer-BERT），GPT→BERT 消融 0.878 acc，128 pytest 全过

### 故事 3：Transformer 解码器

- **S**：BCI 解码传统方法（LDA/CSP）特征工程依赖领域知识，深度学习有望自动提取
- **T**：实现一个现代 Transformer 架构用于 EEG 解码
- **A**：GPT 风格因果 Transformer，RoPE 旋转位置编码，Conv1D Token 嵌入（自适应核大小），Pre-LN + 残差连接，长度自适应推理，AdamW 优化
- **R**：在 PhysioNet MI 数据上完成解码，含数据增强、多长度评估

**行动项**：
- [ ] 每个故事口头练习 2-3 遍，控制在 2 分钟内

---

## 7. 其他速补项

| 项 | 要点 | 优先级 |
|----|------|--------|
| Riemannian Geometry / pyRiemann | 近年 BCI 比赛常胜方法，了解协方差矩阵 + 切空间映射即可 | 低 |
| BCI Competition 数据集 | 4 届比赛数据是面试常见 benchmark | 中 |
| 信息传输率（ITR） | BCI 系统评价指标，公式：ITR = (log2(N) + P*log2(P) + (1-P)*log2((1-P)/(N-1))) * 60/T | 中 |
| EEGNet | 轻量级 CNN，BCI 深度学习基线模型，你 exercises 里已写过 | 低 |
| 脑电生理学基础 | ERP 各成分（P300/N400/P600）、ERD/ERS 生理含义 | 中 |

---

## 补强进度

| # | 项目 | 状态 |
|---|------|------|
| 1 | LSL 协议 | ⬜ 未开始 |
| 2 | 10-20 电极系统 | ⬜ 未开始 |
| 3 | 常见伪迹 | ⬜ 未开始 |
| 4 | CSP 解码器 | ⬜ 未开始 |
| 5 | EEG 硬件设备 | ⬜ 未开始 |
| 6 | STAR 故事 | ⬜ 未开始 |
| 7 | 其他速补 | ⬜ 未开始 |
