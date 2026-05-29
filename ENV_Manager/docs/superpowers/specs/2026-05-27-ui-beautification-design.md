# ENV_Manager UI 美化设计方案

## 目标

对 ENV_Manager 的前端界面进行视觉升级，采用极简 Pro 风格（类似 Ant Design Pro），提升整体质感而不改变功能逻辑。

## 改动范围

仅涉及前端展示层，不改动后端 API 和业务逻辑。

| 文件 | 改动类型 |
|------|---------|
| `frontend/src/App.vue` | 重写样式 + 新增统计卡片 |
| `frontend/src/components/PropsEditor.vue` | CSS 微调 |
| `frontend/src/components/PortEditor.vue` | CSS 微调 |

## 详细设计

### 1. 顶栏（App Header）

- **背景**：`linear-gradient(135deg, #409EFF, #2b7ed6)` 蓝色渐变，白色文字
- **布局**：flex 左右排列，左侧 `el-icon + 标题`，右侧刷新按钮（白色 outline 风格）
- **副标题**：顶栏下方浅灰色描述文字 "管理和监控本地 BI 系统实例"
- **圆角**：10px，轻微阴影

### 2. 统计卡片（Stats Cards）

- **位置**：顶栏下方，表格上方，水平三列等宽
- **三张卡片**：总环境数、运行中、已停止
- **每张卡片内容**：左侧标签+数字，右侧带渐变背景的小图标
- **颜色**：总环境（蓝色#409EFF）、运行中（绿色#67C23A）、已停止（灰色#909399）
- **样式**：白色背景、8px 圆角、1px 细边框 `#f0f0f0`、`box-shadow`

### 3. 状态标签（Status Tag）

用 `el-tag` 替代 `el-tag` 默认样式，自定义外观：

- **运行中**：浅绿背景 `#f0f9eb`，绿色文字 `#67C23A`，左侧 8px 绿色圆点带 CSS `@keyframes pulse` 呼吸动画（`opacity: 1 → 0.5 → 1`，2s 循环）
- **已停止**：浅灰背景 `#f4f4f5`，灰色文字 `#909399`，左侧 8px 灰色静态圆点

### 4. 表格容器（Table Card）

- 将 `el-table` 包裹在 `el-card` 中
- 卡片加标题栏 "环境列表"
- 卡片样式：10px 圆角、1px 细边框、轻微阴影

### 5. 对话框微调

- PropsEditor 和 PortEditor 对话框保持现有结构
- 统一边距和内边距：dialog body padding 改为 20px
- 按钮区域与内容区加分隔线

### 6. 呼吸动画 CSS

```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### 7. 禁用按钮样式

当按钮处于 `:disabled` 状态时，降低透明度并显示为 `not-allowed` 光标，避免与普通文字混淆。

## 不变部分

- 所有功能逻辑、API 调用、数据流完全不改动
- Vue 组件结构和 props/emits 不变
- 响应式数据结构和缓存逻辑不变
- 分属性和编辑器对话框内部交互逻辑不变
