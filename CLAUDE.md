# TestHelper 项目规则

## 运行时规则

1. 在 `C:\Repo\codeRepo\TestHelper` 下运行时，如果用户没有明确要求读取某个子目录，不要主动读取次级目录里的内容。

2. `C:\Repo\codeRepo\TestHelper` 是常规运行目录，其下的子文件夹是各自独立的项目、工具或产物，没有直接的代码依赖关系。

## 常用路径

| 路径 | 用途 |
|------|------|
| `C:\Repo\codeRepo\bi` | 系统代码本地仓库 |
| `C:\Users\cchan\Desktop\Environment` | 环境目录（BI 实例运行目录） |
| `C:\Repo\codeRepo\TestHelper\ENV_Manager` | 管理环境目录的工具 |
| `C:\Repo\codeRepo\TestHelper\MCP` | MCP 服务目录 |

## 图片识别规则（聊天图片钩子）

当用户的输入包含 `[Unsupported Image]`（表示用户发送了图片但主模型无法直接查看）时：

### 图片识别流程

当用户的输入包含 `[Unsupported Image]`：

1. 调用 `process_chat(auto_scan=true)` → 自动取 `MCP/image_temp/latest.png`
2. 工具内部调 Qwen 视觉模型识图 → 返回描述
3. 基于描述回复用户

**前置依赖**：VSCode 扩展 `Chat Image Hook` 已在后台运行，
当用户在聊天面板中复制图片时，自动存到 `image_temp/latest.png`。
每次只保留最新一张，不会堆积。

