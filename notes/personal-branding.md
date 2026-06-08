# 个人品牌与展示优化指南

> 画像：自建型全栈极客——动手驱动、网络栈扎实、DL 有理论深度、数学底子好
> 目标：让网站如实反映这个画像，不偏向任何单一方向

---

## 核心原则

- **忠于画像**：你是"什么都自己搭、深入原理、数学+DL 底子好"的人，网站传达这个
- **不为单一岗位服务**：BCI、生信、网络都只是你能力的侧面
- **访客视角**：5 秒内知道"这个人做什么、擅长什么"
- **内容为王**：项目 > 博客 > 标签
- **诚实但不自曝短板**

---

## 1. 已完成的修改

| 文件 | 改动 |
|------|------|
| `about.yaml` | 删除"考研失败"；生涯改为三段工作经历；标签改为"自建一切/科学计算+DL/Linux+网络栈/数学底子/问题驱动"；技能重排（Python/PyTorch/Linux/Docker/Git 在前）；身份改为"软件工程师" |
| `_config.yml` | 标题→`Shane Hu`；副标题→"自建 · 深入原理 · 科学计算" |
| `_config.solitude.yml` | 侧边栏→"自建一切 · 深入原理 · 科学计算"；导航加"项目作品"入口 |
| `projects/index.md` | 新建项目页，三个项目按真实能力维度展示 |
| `_posts/rnaseq-pipeline-engineering.md` | 新博客：Snakemake 自研框架 |
| `_posts/transformer-eeg-decoding.md` | 新博客：GPT 风格 Transformer 解码 EEG |
| `_posts/eeg-signal-processing-toolchain.md` | 新博客：从零搭端到端 EEG 工具链 |
| 网站已部署 | `hexo deploy` 成功，https://hs3434.github.io 已更新 |

---

## 2. 待完成

### 🔴 紧急

- [x] 本地预览确认改动效果（`npx hexo server`）
- [x] 部署上线（`npx hexo deploy`）

### 🟡 重要（1 周内）

#### 写 2-3 篇新博客

- [x] 《自研 Snakemake 框架：不满设计就自己改》→ 已写 `rnaseq-pipeline-engineering.md`
- [x] 《GPT 风格 Transformer 解码 EEG》→ 已写 `transformer-eeg-decoding.md`
- [x] 《从零搭一套端到端信号处理工具链》→ 已写 `eeg-signal-processing-toolchain.md`

写作要点：
- 不仅说"做了什么"，要说"**为什么这么设计**"
- 配图：架构图、截图、结果
- 代码片段：贴核心 10-20 行

#### 项目页加截图/GIF

- 截 BCI GUI 关键界面
- 录 GIF 演示（30 秒）
- 放在 `/img/projects/` 下

#### 博客标签/分类优化

| 文章 | 补充标签 |
|------|---------|
| Transformer 从入门到上手 | `deep-learning` `pytorch` |
| DNS / 53 端口 / dnscrypt-proxy | `network` `linux` |
| Dante socks5 | `network` `linux` |
| HTTP 307 缓存 | `web` `network` |
| udesk API | `python` `api` |
| 高等代数笔记 | `mathematics` |

新增分类建议：`deep-learning`、`network`

### 🟢 加分

- [ ] GitHub Profile README（`hs3434/hs3434`），基于画像写：

```markdown
### Hi, I'm Shane Hu

🛠 Build everything from scratch — pipelines, GUIs, network stacks  
🔬 Deep into how things work — Transformer internals, signal processing, linear algebra  
🐧 Linux, networking, Docker — self-hosted everything

📌 [BCI Toolkit](https://github.com/hs3434/bci-pipeline) — Full-stack EEG analysis tool  
📖 [Blog](https://hs3434.github.io)

📫 hs3434@foxmail.com
```

- [ ] 推 bci-pipeline 仓库 + README（架构图 / Quick Start / GIF）
- [ ] Pin 4 个代表仓库
- [ ] 简历页 /resume（可选）
- [ ] LinkedIn / 掘金 / 知乎 同步
- [ ] 项目 demo 视频

---

## 3. 整体路标

| 阶段 | 时间 | 产出 |
|------|------|------|
| 🔴 紧急 | 1-2 天 | 预览确认 + 部署上线 |
| 🟡 重要 | 1 周 | 2 篇新博客 + 截图/GIF + 标签优化 |
| 🟢 加分 | 2 周 | GitHub Profile + 仓库整理 + 平台同步 |
