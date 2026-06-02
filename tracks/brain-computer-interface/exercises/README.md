# BCI 学习路线 — Exercises 总结

## Week 1 — Python 科学计算基础

**内容**：NumPy 数组操作、Pandas 表格处理、SciPy 滤波器设计（Butterworth + filtfilt 零相位滤波）、Matplotlib 可视化入门、综合串联完整 EEG 处理流程（Raw → 滤波 → Epochs → 可视化 → 导出）。

**核心技能**：ndarray 广播与向量化、DataFrame loc/iloc/GroupBy、滤波器 freqz/filtfilt、EEG 时域/频域可视化。

---

## Week 2 — Qt GUI 开发

**内容**：Qt 信号槽机制、自定义信号 `pyqtSignal`、`QMainWindow` 结构与菜单/工具栏、`QThread` 后台 worker 模式（避免 UI 阻塞）、Matplotlib 嵌入 Qt（`FigureCanvasQTAgg` + `QTimer` 实时更新）、文件对话框（`QFileDialog`）与自定义 `QDialog`。

**核心技能**：Qt MVC 架构、线程安全信号通信、`FigureCanvasQTAgg` 集成、性能优化（`draw_idle` vs `draw`、降采样）。

---

## Week 3 — EEG 信号处理原理

**内容**：时域统计（均值/RMS/方差）→ 傅里叶变换（DFT/FFT）→ 频域分析（PSD、Welch 方法）→ 频谱泄漏与窗函数（Hann/Hamming/Blackman）→ 数字滤波器（IIR/FIR、Butterworth）→ STFT 时频分析 → 小波变换 + ICA 伪迹去除。

**核心技能**：FFT 频谱分析、滤波器设计与相位补偿、STFT 时间-频率权衡、ERD/ERS 检测、ICA 眼动/肌电伪迹分离。

---

## Week 4 — MNE-Python 全流程

**内容**：`Raw → Epochs → Evoked` 数据结构、坏道检测/重参考/ICA 伪迹去除、事件检测与 Epoch 提取、ERD/ERS 时频分析（Alpha/Beta 频段）、LDA 分类器与交叉验证。

**核心技能**：`mne.io.read_raw_*`、`mne.events_from_annotations`、epoch 窗提取与基线校正、时频能量计算、CSP/LDA 解码。

---

## Week 5 — BCI 范式与解码

**内容**：

| 范式 | 解码方法 |
|------|----------|
| **SSVEP** | CCA、FBCCA（滤波器组 CCA）频域检测 |
| **运动想象** | ERD/ERS、CSP（共同空间模式） |
| **P300** | 事件相关电位 (~300ms)、行列刺激范式、ITR 计算 |
| **深度学习** | EEGNet CNN 架构、数据增强 |

**核心技能**：频域 CCA 相关分析、CSP 空间模式提取、P300 信号平均、CNN 端到端训练。

---

## Week 6 — BCI GUI 应用开发

**内容**：MVC 架构、Qt 组件层次、`QThread` 异步处理、事件/Epoch 标记界面、实时 EEG 波形绘制、分类结果可视化（混淆矩阵 + ITR）、头皮地形图（Alpha/Beta 频段功率分布）、多格式导出（CSV/NumPy/FIF/Pandas）与 HTML 报告生成（Jinja2）。

**核心技能**：`QSplitter` 多面板布局、Qt 异步架构、实时滚动缓冲区、`mne.viz.plot_topomap`、报告自动生成。

---

## Week 7 — 工程化与生产级代码

**内容**：模块化设计（高内聚低耦合）、dataclass 配置 + YAML、`logging` 日志系统、异常层级、pytest 单元测试（fixtures/parametrize/mock）+ GitHub Actions CI、类型注解与文档（Sphinx/mkdocs）、`pyproject.toml` 打包发布。

**核心技能**：项目结构分层、配置外部化、自动化测试、文档自动化、包版本管理与分发。

---

## 学习路径总览

```
Week1: NumPy/SciPy/Matplotlib 基础
Week2: Qt GUI 开发（信号槽、线程、Matplotlib 集成）
Week3: EEG 信号处理原理（FFT、滤波、STFT、ICA）
Week4: MNE-Python 全流程（Raw → Epochs → Evoked → Decode）
Week5: BCI 三大范式（SSVEP/MI/P300）+ 深度学习
Week6: Qt GUI 实战（实时波形、topomap、结果可视化、报告导出）
Week7: 工程化（模块化、日志、测试、CI、文档、打包）
```

从数据处理底层到 GUI 应用上层，从理论到工程，循序渐进构建 BCI 软件开发能力。