# Day 3：插件机制分析

## 今日目标
理解 OpenCode 的插件系统、如何注册插件、插件 API

## 学习资料

### 英文（主要）
- [OpenCode Plugin API](https://github.com/anomalyco/opencode/tree/main/docs/plugins.md)（如果有）

### 中文（辅助）
- 查看 plugins/ 目录

## 理论学习（1小时）

### 插件目录结构
```
opencode/
├── plugins/                  # 内置插件
│   ├── clipboard/
│   ├── terminal/
│   └── ...
```

### 插件接口（推测）
```typescript
// plugins/my-plugin/src/index.ts

// 插件元信息
export const pluginMeta = {
  name: 'my-plugin',
  version: '1.0.0',
  description: 'My custom plugin',
};

// 插件主类
export class MyPlugin {
  constructor(config: PluginConfig) {
    this.config = config;
  }

  // 生命周期
  async onLoad(context: PluginContext) {
    // 插件加载时调用
  }

  async onUnload() {
    // 插件卸载时调用
  }

  // 注册命令
  registerCommands(registry: CommandRegistry) {
    registry.register('my-command', this.executeCommand.bind(this));
  }

  // 注册适配器
  registerAdapter(registry: AdapterRegistry) {
    registry.register('my-model', this.myModelAdapter);
  }
}
```

### 插件配置
```json
// opencode.config.json
{
  "plugins": [
    {
      "name": "clipboard",
      "enabled": true
    },
    {
      "name": "my-plugin",
      "enabled": true,
      "config": {
        "option": "value"
      }
    }
  ]
}
```

## 练手项目（1.5小时）

### 项目：Week4 OpenCode Debug - 插件分析

**需求**：

```bash
# 1. 查看插件目录
ls -la opencode/plugins/ 2>/dev/null || echo "No plugins dir, check packages/"

# 2. 搜索插件相关代码
grep -r "plugin" opencode/packages/core/src/ --include="*.ts" | head -30

# 3. 查看是否有 plugin 接口定义
find opencode -name "*plugin*.ts" -o -name "*plugin*.d.ts" 2>/dev/null

# 4. 分析一个内置插件（如果有）
ls opencode/packages/*/src/plugins/ 2>/dev/null || true
```

**分析内容**：
```markdown
# OpenCode 插件机制分析

## 插件目录
-

## 插件接口
-

## 内置插件
-

## 注册机制
-
```

## 调试复盘（0.5小时）

### 验证方式
```bash
# 搜索插件注册相关代码
grep -r "registerPlugin\|addPlugin\|loadPlugin" opencode --include="*.ts" | head -10
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 找到插件目录结构
- [ ] 理解插件接口定义
- [ ] 分析内置插件实现
- [ ] 理解插件注册机制
- [ ] 记录分析结果
