# ENV_Manager - 本地 BI 系统管理工具

基于 Python Flask + Vue 3 的本地 Web 管理工具，用于管理 Windows 环境下多个 Java+Tomcat BI 系统的启停和配置修改。

## 功能

- **启动/停止** — 调用 startup.bat / shutdown.bat 管理系统实例，支持端口检测确认 + taskkill 强制杀进程
- **一键访问** — 浏览器打开运行中系统的 BI 访问地址
- **Jar 目录** — 在资源管理器中打开对应环境的 product 目录
- **日志目录** — 在资源管理器中打开对应环境的 vividime/log 目录
- **Properties 编辑** — 在线 CRUD db.properties / bi.properties，保存前自动备份为 `.bak`
- **端口配置** — 修改 server.xml 的 Shutdown port / Connector port
- **调试端口** — 管理 catalina.bat 的 JVM 调试端口（增、改、删）
- **环境信息复制** — 点击端口号一键复制环境信息到剪贴板

## 技术栈

| 层面 | 技术 |
|------|------|
| 后端 | Python 3 + Flask + Waitress |
| 前端 | Vue 3 + Vite + Element Plus + Axios |
| 服务端口 | 6688 |

## 环境结构

所有 BI 系统位于 `C:\Users\cchan\Desktop\Environment\`，每个系统独立文件夹：

```
Environment/
├── 10.0/
├── 10.1/
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
│   │   ├── startup.bat          # 启动脚本
│   │   ├── shutdown.bat         # 停止脚本
│   │   └── catalina.bat         # JVM 参数 + 调试端口
│   └── conf/
│       └── server.xml            # 端口配置
├── vividime/                     # 11.x 版本使用（优先）
│   ├── db.properties
│   ├── bihome/
│   │   └── bi.properties
│   └── product/                  # jar 包目录
├── vividime/log/                 # 日志目录
└── Yonghong/                     # 10.x 版本使用（备选）
    ├── db.properties
    ├── bihome/
    │   └── bi.properties
    └── product/                  # jar 包目录
```

## 项目结构

```
ENV_Manager/
├── backend/
│   ├── app.py                    # Flask 入口，注册蓝图与路由
│   ├── config.py                 # 配置文件（路径常量、端口等）
│   ├── requirements.txt          # Python 依赖
│   └── modules/
│       ├── __init__.py
│       ├── env_discovery.py      # 扫描 Environment 目录发现系统
│       ├── tomcat_ctl.py         # 启停控制（startup.bat / shutdown.bat + taskkill）
│       ├── props_editor.py       # properties 文件 CRUD（自动备份）
│       ├── server_xml.py         # server.xml 端口读取/修改
│       └── catalina_editor.py    # catalina.bat 调试端口管理
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js               # Vue 入口 + Element Plus 注册
│       ├── App.vue               # 根组件（环境列表表格）
│       ├── api/
│       │   └── index.js          # Axios API 封装
│       └── components/
│           ├── PropsEditor.vue   # properties 键值对编辑器
│           └── PortEditor.vue    # 端口 + 调试端口编辑器
├── start-dev.bat                 # 开发模式启动脚本
└── start.bat                     # 生产模式启动脚本（桌面快捷方式）
```

## 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+

### 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 运行

#### 开发模式（前后端分离，支持热更新）

```bash
start-dev.bat
```

或分别启动：

```bash
# 终端 1：后端
cd backend && python app.py

# 终端 2：前端
cd frontend && npm run dev
```

- 后端 API：http://localhost:6688
- 前端页面：http://localhost:5173（自动代理 API 请求到后端）

#### 生产模式（单服务运行）

```bash
start.bat
```

或手动执行：

```bash
cd frontend && npm run build
cd backend && python app.py --serve-frontend
```

- 访问 http://localhost:6688

### 桌面快捷方式

桌面 `ENV_Manager.bat` 双击即可启动（托盘模式，无持久黑窗）：
- 构建前端 → 启动后台 → 右下角出现扳手图标
- 双击扳手图标 → 浏览器打开管理页面
- 右键扳手图标 → Quit 退出

如需传统有窗口模式，直接运行 `start.bat`。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/envs` | 获取所有环境列表及运行状态 |
| POST | `/api/envs/{version}/start` | 启动环境 |
| POST | `/api/envs/{version}/stop` | 停止环境 |
| GET | `/api/envs/{version}/access-url` | 获取访问地址 |
| POST | `/api/envs/{version}/open-jar` | 在资源管理器中打开 jar 目录 |
| POST | `/api/envs/{version}/open-log` | 在资源管理器中打开日志目录 |
| GET | `/api/envs/{version}/props/{file}` | 获取 properties 全部键值对 |
| PUT | `/api/envs/{version}/props/{file}` | 批量保存 properties（全量覆盖） |
| DELETE | `/api/envs/{version}/props/{file}/{key}` | 删除指定参数 |
| GET | `/api/envs/{version}/server-ports` | 获取端口配置 |
| PUT | `/api/envs/{version}/server-ports` | 修改端口 |
| GET | `/api/envs/{version}/debug-port` | 获取调试端口 |
| PUT | `/api/envs/{version}/debug-port` | 新增或修改调试端口 |
| DELETE | `/api/envs/{version}/debug-port` | 删除调试端口 |

## 配置

编辑 `backend/config.py`：

- `ENVIRONMENT_ROOT` — 环境根目录路径
- `API_PORT` — 服务端口号（默认 6688）

## 注意事项

- 端口 6688 曾使用 6666，因 Chrome 将 6666 列入不安全端口列表（ERR_UNSAFE_PORT）而更换
- db.properties 在系统首次启动前不存在，编辑器会提示"需要启动系统来创建此文件"
- 停止环境采用两步策略：先 `shutdown.bat` 优雅关闭，失败则通过 `netstat` + `taskkill` 强制杀进程
- 启动端口检测使用并行探测（线程池），8 个环境约 0.3 秒完成刷新
