# 本地 BI 系统管理页面设计文档

## 概述

基于 Python Flask + Vue 3 (Vite) 构建的本地 Web 管理系统，用于管理 Windows 环境下多个 Java+Tomcat BI 系统的启停、配置修改等操作。

## 环境结构

所有 BI 系统位于 `C:\Users\cchan\Desktop\Environment\`，每个系统独立文件夹：

```
Environment/
├── 10.0/           # version = 10.0
├── 10.1/           # version = 10.1
├── 10.1.4.1/
├── 10.2/
├── 11.0/
├── 11.1/
├── 11.1Fabric/
└── 11.2/
```

每个系统的目录结构：

```
{version}/
├── tomcat/
│   ├── bin/
│   │   ├── startup.bat       # 启动脚本
│   │   ├── shutdown.bat      # 停止脚本
│   │   └── catalina.bat      # JVM 参数 + 调试端口配置
│   └── conf/
│       └── server.xml         # 端口配置
├── vividime/                  # 11.x 版本使用（优先）
│   ├── db.properties
│   ├── bihome/
│   │   └── bi.properties
│   └── product/               # jar 包目录
└── Yonghong/                  # 10.x 版本使用（备选）
    ├── db.properties
    ├── bihome/
    │   └── bi.properties
    └── product/               # jar 包目录
```

## 技术栈

| 层面 | 技术 | 说明 |
|------|------|------|
| 后端 | Python 3 + Flask + Waitress | RESTful API，生产模式用 Waitress 部署 |
| 前端 | Vue 3 + Vite | 前后端分离 SPA |
| UI 组件库 | Element Plus | 美观易用的组件 |
| HTTP 客户端 | Axios | 前后端通信 |
| 服务端口 | 6688 | 固定端口（原 6666 被 Chrome 拦截） |

## 项目结构

```
ENV_Manager/
├── backend/
│   ├── app.py                      # Flask 入口，注册路由
│   ├── config.py                   # 配置文件（路径常量等）
│   ├── requirements.txt
│   └── modules/
│       ├── __init__.py
│       ├── env_discovery.py        # 扫描 Environment 目录发现系统
│       ├── tomcat_ctl.py           # 启停控制（startup.bat / shutdown.bat + taskkill）
│       ├── props_editor.py         # properties 文件 CRUD（db.properties, bi.properties）
│       ├── server_xml.py           # server.xml 端口读取/修改
│       └── catalina_editor.py      # catalina.bat 调试端口管理
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js                 # Vue 入口
│       ├── App.vue                 # 根组件（环境列表表格）
│       ├── api/
│       │   └── index.js            # Axios API 封装
│       └── components/
│           ├── PropsEditor.vue     # properties 键值对编辑器（弹窗）
│           └── PortEditor.vue      # 端口 + 调试端口编辑器（合并弹窗）
├── start-dev.bat                   # 开发模式启动脚本
└── start.bat                       # 生产模式桌面快捷启动脚本
```

## 后端 API 设计

### 环境管理

```
GET    /api/envs                     → 获取所有环境列表及运行状态
POST   /api/envs/{version}/start     → 启动环境（运行 startup.bat）
POST   /api/envs/{version}/stop      → 停止环境（shutdown.bat + taskkill 兜底）
GET    /api/envs/{version}/access-url → 获取访问地址
POST   /api/envs/{version}/open-jar  → 资源管理器打开 jar 目录
```

### db.properties / bi.properties CRUD

```
GET    /api/envs/{version}/props/{file}            → 所有键值对（file = db 或 bi）
PUT    /api/envs/{version}/props/{file}            → 批量保存（全量覆盖）
PUT    /api/envs/{version}/props/{file}/{key}      → 更新指定 key
DELETE /api/envs/{version}/props/{file}/{key}      → 删除指定 key
```

- `{file}` 传 `db` 或 `bi`
- 后端自行处理路径查找逻辑（优先 vividime → 回退 Yonghong）
- 保存前自动备份为 `xx.properties.bak`

### server.xml 端口管理

```
GET    /api/envs/{version}/server-ports  → {"shutdown_port": 9101, "connector_port": 8101}
PUT    /api/envs/{version}/server-ports  → 修改端口
```

### catalina.bat 调试端口管理

```
GET    /api/envs/{version}/debug-port    → {"debug_port": 8075} 或 {"debug_port": null}
PUT    /api/envs/{version}/debug-port    → 新增或修改调试端口
DELETE /api/envs/{version}/debug-port    → 删除调试端口配置
```

## 前端页面设计

### 主页面 — 环境列表表格

Element Plus `el-table` 实现，每行一个环境：

| 列 | 内容 |
|------|------|
| Version | 文件夹名（如 11.1、10.1） |
| 状态 | 运行中/已停止（带图标标签） |
| 访问端口 | 可点击的端口号，点击复制环境信息到剪贴板 |
| 操作按钮 | [启动] [停止] [访问] [Jar] |
| 配置入口 | [db] [bi] [端口] |

页面加载时先展示 sessionStorage 缓存数据，后台异步拉取最新数据刷新。

### 配置弹窗

- **db/bi 编辑器** (`PropsEditor.vue`)：`el-dialog` + `el-table` 展示键值对列表，支持行内编辑、删除、新增行，保存时备份并写回文件。对话框 850px 宽，最大高度 90vh，表头固定内容滚动。
- **端口编辑器** (`PortEditor.vue`)：`el-dialog` + `el-input` 编辑 Tomcat 端口（Shutdown port / Connector port），同时在同一弹窗内管理调试端口（增、改、删）。无访问地址展示区域。

## 关键实现细节

### 启停机制

- **启动**：通过 `subprocess.Popen` 执行 `startup.bat`，不捕获输出（黑窗正常显示），等待数秒后通过端口检测确认启动成功
- **停止**：两步策略 — 先 `shutdown.bat` 等待 3 秒优雅关闭，若端口仍在监听则通过 `netstat -ano | findstr` 查找 PID → `taskkill /f /pid` 强制杀进程
- **状态判断**：通过 socket 探测 Connector 端口判断运行状态，8 个环境并行检测（`ThreadPoolExecutor` + 0.3 秒超时），总耗时约 0.3 秒

### Properties 文件查找与备份

- **查找逻辑**：先检查 `vividime/` 目录下是否存在目标文件，不存在则检查 `vividime/bihome/`，再检查 `Yonghong/`，最后 `Yonghong/bihome/`
- **备份逻辑**：保存修改前，将当前文件复制为 `xx.properties.bak`
- **不存在处理**：db.properties 不存在时，API 返回特定错误码，前端弹窗提示"需要启动系统来创建 db.properties"

### catalina.bat 调试端口管理

- **查找**：读取文件内容，搜索 "Xdebug" 关键词，匹配 `address=192.168.151.77:(\d+)` 提取端口
- **添加**：在第一个 `set CATALINA_OPTS` 行后插入调试行
- **修改**：找到现有调试行，替换端口号
- **删除**：移除调试行

### 前端缓存

- 环境列表数据存入 `sessionStorage`，页面加载时先展示缓存数据，再异步拉取最新数据
- 缓存 key 为 `testhelper_envs`

## 启动方式

### 开发模式

前端 Vite dev server + 后端 Flask 分别启动，Vite 代理 `/api` 请求到 Flask。

`start-dev.bat`：

```bat
@echo off
chcp 65001 >nul
cd /d C:\Users\cchan\Desktop\Work\TestHelper\ENV_Manager

start "ENV_Manager-Backend" cmd /c "cd backend && python app.py"
start "ENV_Manager-Frontend" cmd /c "cd frontend && npm run dev"

timeout /t 3 >nul
start http://localhost:5173
```

- 后端 Flask → 端口 6688
- 前端 Vite dev server → 端口 5173（自动代理 `/api` 到 `localhost:6688`）

### 生产模式

一次构建前端，Flask 使用 Waitress 托管前端静态文件，只需启动一个服务。

`start.bat`（桌面快捷方式，日常用）：

```bat
@echo off
chcp 65001 >nul
cd /d C:\Users\cchan\Desktop\Work\TestHelper\ENV_Manager

echo [ENV_Manager] 构建前端...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo [ENV_Manager] 前端构建失败，请检查代码
    pause
    exit /b 1
)

echo [ENV_Manager] 启动服务 (端口 6688)...
cd /d C:\Users\cchan\Desktop\Work\TestHelper\ENV_Manager\backend
start "ENV_Manager" python app.py --serve-frontend

timeout /t 2 >nul
start http://localhost:6688
```

### 后端启动参数

| 模式 | 命令 | 说明 |
|------|------|------|
| 开发 | `python app.py` | 仅启动 API 服务（Flask 内置服务器） |
| 生产 | `python app.py --serve-frontend` | API + 前端静态文件（Waitress 部署） |
