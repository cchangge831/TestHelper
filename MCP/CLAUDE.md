# MCP 服务项目规范

## 项目定位

TestHelper MCP 服务 — 通过 MCP 协议（Model Context Protocol）为 AI 助手提供本地工具能力。通过 stdio 与 AI 客户端（如 Claude Code）通信。

当前功能：
- **识图**：调用通义千问 DashScope 视觉模型（qwen-vl-max）解析图片内容
- **浏览器控制**：基于 Playwright 的浏览器自动化 + 连接到用户已有 Chrome 分析页面

设计原则：**高度可扩展**，新增工具无需修改 `server.py`，只需在 `tools/` 下加模块 + 一行注册。

## 技术栈

| 层 | 技术 | 约束 |
|---|---|---|
| 协议 | MCP (JSON-RPC over stdio) | `mcp` Python SDK |
| 识图 | DashScope API (OpenAI 兼容) | 默认模型 qwen-vl-max |
| 浏览器 | Playwright (async API) | Chromium / Chrome CDP |

## 架构规则

### 工具模块规范

每个 `tools/` 下的模块必须导出：
- `TOOLS: list[dict]` — 工具定义列表（name / description / inputSchema）
- `async handle_tool(name: str, arguments: dict) -> list` — 工具处理函数，返回 MCP content 列表

工具不匹配时返回 `None`（而非报错），让注册中心尝试下一个模块。

### 注册规则

- `tools/__init__.py` 是唯一的工具注册中心
- 新增工具 = 创建 `tools/new_feature.py` + 在 `__init__.py` 的 `_MODULES` 列表加一行 import
- `server.py` 完全不感知具体工具有哪些，只做 `list_tools → get_all_tools()` / `call_tool → handle_tool()` 转发

### 配置规则

- `config.py` 从 `config/config.properties` 读取运行参数
- **敏感信息（API Key 等）从环境变量读取**，不写入配置文件
- 缺项用硬编码默认值
- 配置访问使用函数接口（如 `qwen_api_key()`），不用属性

### 编码规范

- Python 3.10+，类型注解
- 异步函数用 `async def`，阻塞 I/O 用 `await`
- 工具返回统一格式：`list[dict]`，每个 dict 为 `{"type": "text", "text": str}` 或 `{"type": "image", "data": base64, "mimeType": "image/png"}`
- 错误消息前缀 `ERROR: ` 便于 AI 识别

## 目录结构

```
MCP/
├── CLAUDE.md                 ← 本文件
├── server.py                 ← MCP 服务主入口（不感知具体工具）
├── config.py                 ← 配置加载
├── requirements.txt          ← pip 依赖
├── config/
│   └── config.properties     ← 运行时参数
└── tools/
    ├── __init__.py            ← 工具注册中心
    ├── image_analyzer.py      ← 识图工具
    └── browser_ctl.py         ← 浏览器控制工具
```

## MCP 工具清单

| 工具名 | 模块 | 用途 |
|--------|------|------|
| `process_chat` | chat_hook | **聊天图片钩子**：处理图片消息（支持 image_path / image_base64 / auto_scan） |
| `analyze_image` | image_analyzer | 调用通义千问视觉模型分析图片（支持文件路径和 base64） |
| `browser_connect` | browser_ctl | 连接到已有 Chrome 实例 |
| `browser_navigate` | browser_ctl | 导航到 URL |
| `browser_screenshot` | browser_ctl | 截图（整页/元素） |
| `browser_click` | browser_ctl | 点击元素 |
| `browser_type` | browser_ctl | 输入文本 |
| `browser_get_content` | browser_ctl | 获取页面文本内容 |
| `browser_get_console` | browser_ctl | 获取控制台日志 |
| `browser_evaluate` | browser_ctl | 执行 JavaScript |
| `browser_close` | browser_ctl | 关闭浏览器 |

## 聊天图片钩子机制（process_chat）

**问题**：用户在聊天中发送图片时，主模型（非视觉模型）只能看到 `[Unsupported Image]`，无法理解图片内容。

**解决方案**：`process_chat` 工具作为 pre-processing hook：
1. 用户将图片保存到本地文件
2. AI 助手检测到 `[Unsupported Image]`，自动调用 `process_chat`
3. 工具内部调用 `analyze_image`（通义千问视觉模型）识别图片内容
4. 返回「图片描述 + 用户文字」的组合文本，主模型即可正常理解和回复

**使用流程示例**：
```
用户: [粘贴了一张报错截图] 这个错误怎么解决？
AI:   检测到 [Unsupported Image]，先调用 process_chat
      → image_path: "c:\...\screenshot.png"
      → user_text: "这个错误怎么解决？"
      → 获得图片描述 + 用户文字
      → 基于完整信息回答用户问题
```

**局限性**：
- 此钩子在 **工具层面** 实现，无法真正拦截聊天消息
- 需要 AI 助手主动调用 `process_chat` 工具
- 真正的前置拦截需要修改 IDE/Client 层（VSCode 扩展）

## MCP 客户端配置

在 Claude Code 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "testhelper": {
      "command": "python",
      "args": ["C:\\Repo\\codeRepo\\TestHelper\\MCP\\server.py"],
      "env": {
        "QWEN_API_KEY": "sk-xxxxxxxx"
      }
    }
  }
}
```

## 新增工具示例

```python
# tools/new_feature.py

TOOLS = [
    {
        "name": "my_tool",
        "description": "工具描述",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "参数说明"},
            },
            "required": ["param1"],
        },
    },
]

async def handle_tool(name: str, arguments: dict) -> list:
    if name == "my_tool":
        return [{"type": "text", "text": f"处理结果：{arguments['param1']}"}]
    return None  # 不匹配时返回 None，不报错
```

然后在 `tools/__init__.py` 中：
```python
from tools import new_feature

_MODULES = [
    ...,
    new_feature,  # 加一行即可
]
```

## 前置依赖

1. **QWEN_API_KEY**（识图功能需要）：设置环境变量 `QWEN_API_KEY=sk-xxx`，从 [DashScope](https://dashscope.console.aliyun.com/) 获取
2. **Playwright 浏览器**：`playwright install chromium`
3. **Chrome 远程调试**（连接已有 Chrome 需要）：启动 Chrome 时加 `--remote-debugging-port=9222`
