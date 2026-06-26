# 简历 PDF 导出指南（amd-rocm 专用）

> **适用文件**：`tracks/amd-rocm-python-backend/notes/resume.md` → `resume.pdf`
> **更新日期**：2026-06-26
> **使用工具**：pandoc + google-chrome headless

---

## ⚠️ 不要用 weasyprint 导此简历

**weasyprint 69.0 + Noto Sans CJK SC 字体子集化有 bug**：

- 即使加 `--full-fonts` 也不修复
- PDF 内嵌了 Noto-Sans-CJK-SC 字体，但 subset 后丢失 CJK 字形 → 显示方块
- 已 commit `bee33fa` 切换到 chrome 方案

**症状**：PDF 打开后所有中文显示为 □ 方块。

---

## ✅ 推荐导出方式：pandoc + chrome

### 前置依赖

```bash
which pandoc google-chrome
```

如未装：

```bash
sudo apt install pandoc         # 已有
# google-chrome 来自 snap 或 apt，无需额外装
```

### 导出命令（在 `notes/` 目录下）

```bash
cd /work/run/projects/bio-24/my_projects/learning-journey/tracks/amd-rocm-python-backend/notes/

# 1) pandoc 转 markdown → HTML（standalone 模式）
pandoc resume.md -o resume.html --standalone --css resume.css

# 2) google-chrome headless 渲染 HTML → PDF
google-chrome --headless --disable-gpu --no-sandbox \
  --no-pdf-header-footer \
  --print-to-pdf=resume.pdf \
  file://"$(realpath resume.html)"

# 3) 清理中间 HTML
rm -f resume.html

# 4) 验证
pdfinfo resume.pdf | grep -E "Pages|Producer"
ls -la resume.pdf
```

### 预期输出

```
Producer:        Skia/PDF m144
Pages:           2-3
File size:       ~800KB
```

### 验证中文渲染

```bash
pdftoppm -r 100 -png -f 1 -l 1 resume.pdf /tmp/check
```

打开 `/tmp/check-1.png`，确认：
- "胡盛" 标题可见（不是方块）
- 表格、列表、链接正常
- 排版接近 BCI 简历风格

---

## 🔧 排错清单

| 问题 | 原因 | 修复 |
|------|------|------|
| 顶部出现 `6/26/26, 8:20 PM` + 底部 `1/3` | chrome 默认 header/footer | 加 `--no-pdf-header-footer` |
| 顶部出现 "Shane Hu" 大标题 | pandoc 自动插入 title | 改 `resume.md` 第一行 `# 胡盛`，加 `<!-- title: -->` 注释或调整 yaml metadata |
| 中文是方块 | 用了 weasyprint | 切换到 chrome 方案 |
| PDF 大小 > 5MB | chrome 嵌入了完整字体 | 正常（825KB ~ 16MB 都可接受） |
| chrome 报 `inotify_init() failed` | 系统限制 | 警告可忽略，PDF 仍能生成 |
| chrome 报 `Failed to connect to the bus` | dbus 不可用 | 警告可忽略，PDF 仍能生成 |

---

## 📦 字体说明

系统已有 `fonts-noto-cjk` 包（apt 装的官方包），含：
- `Noto Sans CJK SC`（sans 字体）
- `Noto Serif CJK SC`（serif 字体）
- `Noto Sans Mono CJK SC`（mono 字体）

`fc-list :lang=zh` 应能看到这些字体。如果没看到：

```bash
sudo apt install fonts-noto-cjk
fc-cache -fv
```

---

## 🆚 工具对比

| 工具 | 中文 | 体积 | BCI css | 备注 |
|---|---|---|---|---|
| **google-chrome** ✓ | ✓ | ~800KB | ✓ | **推荐** |
| weasyprint 69.0 | ❌ subset bug | 157KB | ✓ | 不要用 |
| pandoc + xelatex | ✓ | ~150KB | ✗（默认排版）| 字体 OK 但 css 失效 |
| wkhtmltopdf | ? | ? | ✓ | 需 `apt install wkhtmltopdf` |

---

## 🔗 相关 commit

- `bee33fa` — 切换 weasyprint → chrome 方案
- `f7e0b04` — Snakemake 博客链接
- `952283c` — 技术博客段（3 篇 transformer）
- `dee25df` — 尤里卡工作描述改为 rnaseq + helix
- `9cffb97` — 去掉 88% coverage（重复）
- `c2952b3` — BCI 链接改项目仓库

---

## 🔮 后续

- BCI 简历（`tracks/brain-computer-interface/notes/resume.md` → `resume.pdf`）也建议用本方案重导（之前是旧版 weasyprint 生成的，依赖已失效）
- 如简历内容改动 → 重新跑本指南的命令
