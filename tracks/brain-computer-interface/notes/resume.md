# 胡盛

- 电话：188-5665-3017
- 邮箱：hs3434@foxmail.com
- 个人网站：[hs3434.github.io](https://hs3434.github.io)
- 求职意向：**脑机接口软件工程师**

---

## 个人简介

3 年生物信息工程化经验，深耕**科研代码工程化、自动化 Pipeline、Linux 服务端**等方向。
自主完成完整的 **BCI 信号处理与解码系统**（Python + PyQt6 + MNE + PyTorch），覆盖数据加载、预处理、Epoch 切分、SSVEP/MI/Transformer 解码、Qt 双模式 GUI（离线分析 + 实时流式）。
擅长将科研代码模块化、抽象框架，并具备完整的服务端运维与网络栈知识。

---

## 求职技能（按岗位匹配排序）

| 类别 | 技能 |
|------|------|
| **核心语言** | Python（3 年深度使用）、C/C++、R、MATLAB（可读写） |
| **科学计算** | NumPy、SciPy、Pandas、scikit-learn |
| **EEG / BCI** | MNE-Python（Raw/Epochs/Evoked、ICA、ERD/ERS、时频）、SSVEP（CCA/FBCCA）、MI、P300 |
| **信号处理** | IIR/FIR 滤波（Butterworth、Notch）、FFT/Welch PSD、STFT、小波、ICA 去伪迹 |
| **机器/深度学习** | PyTorch、CNN、Transformer（含 RoPE、因果注意力）、LDA、PCA、CSP、交叉验证 |
| **GUI 开发** | PyQt6、QThread 异步、Matplotlib 嵌入、信号槽、自定义控件 |
| **工程化** | 模块化设计、dataclass + YAML 配置、pytest、mypy/pyright、uv/pip、Docker |
| **服务端 / 网络** | Linux、Nginx、Django、TCP/IP、代理、MinIO、MySQL、云原生 |
| **协作工具** | Git、Snakemake、Jinja2、Sphinx |
| **证书 / 语言** | CET-4、普通话二级乙、C1 驾驶证 |

---

## 项目经验

### 🧠 BCI 信号处理与解码系统（个人项目）

> Python + PyQt6 + MNE-Python + PyTorch + scikit-learn ｜ 模块化 + 单元测试

完整的脑电信号处理与 BCI 解码工具，覆盖**离线分析**与**实时流式**双模式。项目结构清晰、可扩展，对应岗位要求的"数据处理工具设计开发 / Pipeline 工程化 / GUI 可视化"。

**核心模块**

- `loader`：基于 MNE，支持 EDF / FIF / EEGLAB / BrainVision **4 种主流 EEG 格式**
- `preprocessor`：带通/Notch 滤波、平均参考、坏导插值、**ICA 伪迹去除**（Infomax）
- `epocher`：事件检测（stim 通道 + annotation 回退）、Epoch 切分、基线校正、幅值剔除
- `processor`：**双引擎**——`OfflineProcessor`（`filtfilt` 零相位）+ `OnlineProcessor`（`lfilter` 因果滤波 + EMA 在线归一化，跨 chunk 保持状态）
- `decoder`：**插件式注册机制**，统一 `fit/predict/save/load` 接口
  - `LDA`：StandardScaler + PCA(0.95) + LDA Pipeline
  - `SSVEP / FBCCA`：CCA 多谐波模板 / 滤波器组加权
  - `CNN`：PyTorch 2D 卷积分类器
  - `Transformer`：**GPT 风格因果 Transformer**，含 RoPE 旋转位置编码、Conv1D Token 嵌入、Pre-LN、AdamW，支持长度自适应推理
- `streaming`：`SlidingWindow` 滚动缓冲 + 可配置决策间隔，实现窗口化在线推理
- `pipeline`：`BCIPipeline` 编排 Load→Preprocess→Epoch→Decode→Save，含 `StratifiedKFold` 交叉验证

**GUI（PyQt6 双 Tab）**

- **离线分析**：4 步骤可视化进度条（Load→Preprocess→Epoch→Decode），`QThread` 后台执行不阻塞 UI
- **实时查看**：Start/Pause/Stop 播放控制、**0.25×–100× 速度调节**、滑窗参数实时配置、可加载训练好的模型在线推理、实时波形 / Welch 频谱 / `mne.plot_topomap` 地形图
- 多 Run Session 自动识别（regex 匹配 `S001R\d+.edf`）、多选对话框
- 中文字体自动检测（WenQuanYi / Noto CJK / SimHei）

**工程化**

- **~1400 LOC pytest** 测试套件（decoder / processor / streaming / GUI worker / tabs / widgets）
- `mypy` + `pyright` 双类型检查，`uv` + `pyproject.toml` 现代包管理
- dataclass + YAML 配置体系，含 `validate()` 和 `to_yaml/from_yaml`

**实验**：在 PhysioNet EEGBCI 运动想象数据与 MNE Sample 听视觉 ERP 数据上完成 LDA / Transformer 解码对比，含数据增强、多长度评估、自动出图 (`transformer_eval/`)。

---

### 🧬 基于 Snakemake 的数据分析工作流框架（在职项目）

> 上海欧易生物 ｜ Python ｜ 框架级抽象

- **问题**：Snakemake 的 rule 语法是静态文本，模块无法随意拼接
- **方案**：抛弃 rule DSL，直接调用其内部接口，**通过代码动态生成 rule 单元**，规范输入输出类型后，任意两个模块即可像积木拼接
- **价值**：把"科研代码模块化、流程随意组合"做到框架级——这正是 BCI 岗位 "**将科研代码（MATLAB/Python）工程化与模块化**" 的核心诉求

---

### ☁️ 欧易云生信平台（在职项目）

> 上海欧易生物 ｜ R / Python / Docker / 云原生

将业务分析流程容器化、云平台化，提供云生信工具技术支持。
线上成果：[欧易云平台](https://cloud.oebiotech.com/#/home)。

---

### 🖥️ Linux 系统与服务端（业余项目）

长期租用 VPS 自建 MinIO / Nextcloud / MySQL 等服务，熟悉 Django + Nginx，了解 TCP/IP、代理服务器搭建。
**与岗位匹配点**：BCI 系统常涉及实验室服务器部署、数据存储、内网通信。

---

## 工作经历

### 上海尤里卡信息科技有限公司 ｜ 生物信息工程师 ｜ 2025.04 - 至今

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
- **跨领域学习力**：从生物信息独立迁移到 BCI，8 周内产出完整可演示工具，覆盖信号处理、解码模型、Qt GUI、实时流处理
- **底层视角**：熟悉 Linux / 网络协议 / 容器，能独立完成部署与运维，可承担系统级工作
