# Day 6-7：自定义功能开发或 Week5 规划

## 周末目标
根据 Day 5 的情况，选择继续深入修复或开始 Week5 准备

## 选择 A：继续 OpenCode 深入

### 自定义功能开发
选择一个力所能及的功能：

```bash
# 选项 1：新增模型配置
# 修改 packages/core/src/config/ 添加自定义模型选项

# 选项 2：日志级别支持
# 在 packages/core/src/services/logger.ts 添加 DEBUG 级别

# 选项 3：本地缓存优化
# 在 packages/core/src/services/cache/ 实现简单的内存缓存
```

### 开发流程
```bash
# 1. 创建功能分支
cd opencode
git checkout -b feat/my-custom-feature

# 2. 实现功能
# 编辑相关文件

# 3. 编译测试
cd packages/core && pnpm build

# 4. 提交
git add .
git commit -m "feat: add my custom feature"

# 5. 切回主分支
git checkout main
```

## 选择 B：Week5 预习准备

### 预习内容
- 阅读 Effect 进阶文档
- 了解 SSE 流式输出的深度实现
- 准备 Week5 项目需求

### 预习任务
```markdown
# Week5 预习笔记

## SSE 深度理解
- 重读 Day 5 的 stream.ts
- 查看 OpenCode 中是否有 SSE 实现

## Effect 进阶
- Layer 深层依赖
- Schema 复杂用法

## Week5 项目准备
- 需求：
- 技术方案：
```

## Week5 规划预览

```markdown
# Week5 主题：Effect 进阶 + SSE 深度

## 关键内容
1. Layer 深层依赖注入
2. Schema 复杂验证
3. SSE 流式输出实现
4. 私有模型插件开发

## 配套项目
OpenCode 私有模型插件
- 接入 orbitai 私有 API
- 支持流式输出
- 自定义模型参数
```

## 复盘（1小时）

### Week 4 整体回顾
```markdown
## Week 4 完成情况

### 源码分析
-

### Bug 修复
-

### 自定义功能
-

### 关键收获
-
```

## 产出检查清单
- [ ] 完成源码分析报告
- [ ] 完成至少一个 bug 修复或功能改进
- [ ] 记录 Week5 预习笔记
- [ ] 更新学习进度
