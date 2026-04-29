# Day 5：找一个 small bug 修复

## 今日目标
在 OpenCode 中找一个力所能及的小 bug 修复

## 学习资料

### 英文（主要）
- OpenCode Issues: https://github.com/anomalyco/opencode/issues

### 中文（辅助）
- 查看未关闭的 issue

## 练手项目（1.5小时）

### 寻找 bug 的方法

```bash
# 1. 查看最近的 issue
cd opencode
git log --oneline -20  # 最近提交
git log --oneline --all | head -50  # 所有分支

# 2. 搜索已知问题
# - 类型错误（TypeScript error）
# - 缺失的 null 检查
# - 简单的逻辑错误
# - 拼写错误

# 3. 用 TypeScript 检查
cd opencode
npx tsc --noEmit 2>&1 | head -50

# 4. 查找 TODO/FIXME
grep -r "TODO\|FIXME\|BUG\|HACK" opencode/packages --include="*.ts" | head -20
```

### 可能的修复方向

1. **TypeScript 类型问题**：找不到的 props、缺失的类型
2. **错误处理**：未捕获的异常、缺失的 catch
3. **边界条件**：undefined/null 检查
4. **配置问题**：默认值的处理

### 修复模板

```markdown
# Bug 修复记录

## 问题描述
-

## 发现位置
-

## 修复方案
-

## 修复前
```typescript
// 问题代码
```

## 修复后
```typescript
// 修复后
```
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd opencode
# 修复后重新编译
cd packages/core && pnpm build

# 运行测试（如果有）
cd opencode && pnpm test 2>&1 | tail -20
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 找到一个可修复的 bug
- [ ] 理解问题原因
- [ ] 实现修复
- [ ] 验证修复有效
- [ ] 记录修复内容
