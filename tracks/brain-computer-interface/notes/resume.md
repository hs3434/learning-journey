# 胡盛

- 电话：188-5665-3017
- 邮箱：hs3434@foxmail.com
- 个人网站：[hs3434.github.io](https://hs3434.github.io)
- 求职意向：**脑机接口软件工程师**

---

## 个人简介

3 年生物信息工程化经验，深耕**科研代码工程化、自动化 Pipeline、Linux 服务端**等方向。
擅长将科研代码模块化、抽象框架，并具备完整的服务端运维与网络栈知识。

---

## 求职技能（按岗位匹配排序）

| 类别 | 技能 |
|------|------|
| **核心语言** | Python、R、Linux shell（3 年深度使用）、C/C++、MATLAB |
| **科学计算** | NumPy、SciPy、Pandas、scikit-learn |
| **EEG / BCI** | MNE-Python（Raw/Epochs/Evoked、ICA、ERD/ERS、时频）、SSVEP（CCA/FBCCA）、**CSP+LDA**、MI、P300、Transformer（GPT 因果 / BERT 双向） |
| **信号处理** | IIR/FIR 滤波（Butterworth、Notch）、FFT/Welch PSD、STFT、小波、ICA 去伪迹 |
| **机器/深度学习** | PyTorch、CNN、Transformer（含 RoPE、因果注意力）、常见机器学习算法、交叉验证 |
| **GUI 开发** | PyQt6、QThread 异步、Matplotlib 嵌入、信号槽、自定义控件 |
| **工程化** | 模块化设计、dataclass + YAML 配置、pytest、mypy/pyright、uv/pip、Docker |
| **服务端 / 网络** | Linux、Nginx、Django、TCP/IP、代理、MinIO、MySQL、云原生 |
| **协作工具** | Git、Snakemake |
| **证书 / 语言** | CET-4、普通话二级乙、C1 驾驶证 |

---

## 项目经验

### 🧠 BCI 信号处理与解码系统（个人demo项目）

> Python + PyQt6 + MNE-Python + PyTorch + scikit-learn ｜ MVP 架构 + 模块化 + 128 个测试

完整的脑电信号处理与 BCI 解码工具，覆盖**离线分析** Pipeline（Load → Preprocess → Epoch → Decode），6 种解码器（含 GPT/BERT Transformer 消融），MVP 架构 GUI。对应岗位要求的"数据处理工具设计开发 / Pipeline 工程化 / GUI 可视化"。

- 详细介绍：[hs3434.github.io/2025/06/08/eeg-signal-processing-toolchain](https://hs3434.github.io/2025/06/08/eeg-signal-processing-toolchain/)
- Transformer 在 EEG 解码中的研究笔记：[hs3434.github.io/2025/06/08/transformer-eeg-decoding](https://hs3434.github.io/2025/06/08/transformer-eeg-decoding/)

**核心模块**

- `source`：`FileSource` 数据源抽象 + 注册式 reader 机制，支持 EDF / FIF / EEGLAB / BrainVision **4 种主流 EEG 格式**
- `domain/preprocessor`：`Preprocessor` 类封装滤波（带通/Notch）、平均参考、坏导插值
- `domain/epocher`：事件检测（stim 通道 + annotation 回退）、Epoch 切分、基线校正、幅值剔除
- `decoder`：**插件式注册机制**，统一 `fit/predict/save/load` 接口，懒加载避免重型依赖
  - `LDA`：StandardScaler + PCA(0.95) + LDA Pipeline
  - `SSVEP / FBCCA`：CCA 多谐波模板 / 滤波器组加权
  - `CSP`：MNE CSP → log-方差特征 → StandardScaler → LDA，MI-BCI 经典 pipeline
  - `CNN`：PyTorch 2D 卷积分类器
  - `Transformer (GPT)`：**因果 Transformer**，含 RoPE 旋转位置编码、Conv1D Token 嵌入、Pre-LN、AdamW，支持长度自适应推理
  - `Transformer (BERT)`：双向注意力 + `[CLS]` head，与 GPT 形成因果/双向消融对比
- `application`：基于 `PipelineSession` 编排 Load→Preprocess→Epoch→Decode，含 `StratifiedKFold` 交叉验证与增量重执行（`invalidate_from` + `_first_invalid` 状态机）；MVP 架构 — `BatchPresenter`（controller）+ `IBatchView` ABC + `RunState` 状态机（IDLE/LOADING/LOADED/RUNNING/COMPLETE/ERROR），worker 工厂可注入便于测试

**GUI（PyQt6 + MVP 架构）**

- 4 步骤可视化进度条（Load → Preprocess → Epoch → Decode），`BatchTab`（view）只负责控件与信号，通过 `IBatchView` 接口全部委托给 `BatchPresenter`（controller）
- 后台执行：`BatchWorker`（QObject）在 `QThread` 中运行，主线程不阻塞；worker 工厂可注入便于测试
- 波形 / Welch 频谱可视化；含 `mne.viz.plot_topomap` 头皮地形图组件
- 多 Run Session 自动识别（regex 匹配 `S001R\d+.edf`）、多选对话框
- 中文字体自动检测（WenQuanYi / Noto CJK / SimHei）

**工程化**

- **128 pytest 测试全过**（decoder / pipeline / presenter / source readers / GUI worker / widgets），覆盖 6 种解码器、MVP 行为、worker 生命周期
- `pyright` 类型检查 + `uv` + `pyproject.toml` 现代包管理
- dataclass + YAML 配置体系，含 `validate()` 和 `to_yaml/from_yaml`

**实验**：在 PhysioNet EEGBCI 运动想象数据与 MNE Sample 听视觉 ERP 数据上完成 **GPT vs BERT 消融**：基线 0.806 → +金字塔增强 0.844 → +双向+`[CLS]` 0.865 → +最优窗口 L=85 **0.878**；CNN 基线 0.944。含数据增强、多长度评估、自动出图。

---

### 🧬 基于 Snakemake 的数据分析工作流框架（在职项目）

> 解螺旋 ｜ Python ｜ 框架级抽象

- **问题**：Snakemake 的 rule 语法是静态文本，模块无法随意拼接
- **方案**：抛弃 rule DSL，直接调用其内部接口，**通过代码动态生成 rule 单元**，规范输入输出类型后，任意两个模块即可像积木拼接
- **价值**：把"科研代码模块化、流程随意组合"做到框架级——这正是 BCI 岗位 "**将科研代码（MATLAB/Python）工程化与模块化**" 的核心诉求

- 详细介绍：[hs3434.github.io/2025/06/08/rnaseq-pipeline-engineering](https://hs3434.github.io/2025/06/08/rnaseq-pipeline-engineering/)
---

### ☁️ 欧易云生信平台（在职项目）

> 上海欧易生物 ｜ R / Python / Docker / 云原生

将业务分析流程容器化、云平台化，提供云生信工具技术支持。
线上成果：[cloud.oebiotech.com](https://cloud.oebiotech.com/#/home)。

---

### 🖥️ Linux 系统与服务端（业余项目）

长期租用 VPS 自建 MinIO / Nextcloud / MySQL 等服务，熟悉 Django + Nginx，了解 TCP/IP、代理服务器搭建。
**与岗位匹配点**：BCI 系统常涉及实验室服务器部署、数据存储、内网通信。

---

## 工作经历

### 解螺旋（上海）科技有限公司 ｜ 生物信息工程师 ｜ 2025.04 - 至今

- 将医学转录组业务开发为**自动化分析流程**
- 在服务器运维部署、代码开发、算法等方面为团队提供技术支持

### 上海欧易生物医学科技有限公司 ｜ 生物信息研发工程师 ｜ 2022.08 - 2024.07

- 负责业务流程**自动化、云平台化**，主导 Snakemake 自研框架
- 为云平台生信工具提供技术支持
- 技术栈：R、Python、Linux、Docker、云原生

### 上海欧易生物医学科技有限公司 ｜ 生物信息实习生 ｜ 2021.10 - 2022.01

- 单细胞转录组质控、常规与个性化分析
- 技术栈：R、Python、Linux

---

## 教育背景

**西北农林科技大学** ｜ 植物科学与技术 ｜ 本科 ｜ 2018.09 - 2022.07 ｜ GPA：3.35

- 毕业论文：《基于逻辑斯蒂回归确定小麦倒伏相关性状及抗倒性状指标》（**早期机器学习实践**）
- 参与：《Rhizobium Inoculation Enhances the Resistance of Alfalfa ... in Copper-Contaminated Soil》（科创项目）

---

## 自我评价

- **强工程化思维**：3 年将科研代码 → 自动化流程 → 平台化的实战经验，恰好对应 BCI 岗位"科研 pipeline 向工程系统转化"的核心职责
- **跨领域学习力**：从生物信息独立迁移到 BCI，8 周内产出完整可演示工具，覆盖信号处理、6 种解码模型、MVP Qt GUI、PyTorch Transformer 消融
- **底层视角**：熟悉 Linux / 网络协议 / 容器，能独立完成部署与运维，可承担系统级工作
