# ENV_Manager 项目规范

## 项目定位

本地 Windows 永洪 BI 系统管理工具。通过 Web UI 管理 `C:\Users\cchan\Desktop\Environment\` 下的 8 个 Java+Tomcat BI 实例（版本 10.0 ~ 11.2）。

## 技术栈

| 层 | 技术 | 约束 |
|---|---|---|
| 后端 | Python 3 + Flask + Waitress | 端口 6688，无数据库 |
| 前端 | Vue 3 + Vite + Element Plus + Axios | 单页面，无路由 |
| 通信 | REST API（JSON） | 前端代理 `/api` → 后端 6688 |

## 架构规则（不可违反）

### 后端

- **所有路由在 `app.py`** — 不使用 Blueprints，项目规模足够小
- **`config.py` 是唯一配置中心** — `ENVIRONMENT_ROOT`、`API_PORT`、路径辅助函数全部在此。不把路径字符串散落在各模块
- **系统参数走 `config.properties`** — 运行时参数（端口、路径等）在 `config/config.properties` 中以 `key=value` 格式定义，`config.py` 优先读取此文件，缺项用硬编码默认值
- **`.properties` 文件转义规则** — 反斜杠用 `\\`，等号用 `\=`（key 中），行首 `#` 用 `\#`；路径中的 `\` 必须写为 `\\`；读写须通过 `modules/config_properties.py` 模块
- **模块职责单一** — `env_discovery.py` 只做环境扫描/端口检测，`tomcat_ctl.py` 只做启停，`props_editor.py` 只做 properties CRUD，以此类推
- **返回 `{"success": bool, "message": str}` 结构** — 启动/停止/写操作统一用此格式；读取操作直接返回数据或 `{"error": str}`
- **带 `--serve-frontend` 参数用 Waitress**，不带则用 Flask dev server（debug=True）
- **文件修改前必须 `.bak` 备份** — `props_editor.py` 和同类模块的写操作都要先备份再覆写
- **批处理文件必须设置 `cwd=`** — `startup.bat`/`shutdown.bat` 的 `subprocess.Popen` 或 `subprocess.run` 必须传入 `cwd=os.path.dirname(script_path)`，否则执行失败
- **停止策略：先 grace shutdown.bat → 等 3s → netstat 查 PID → taskkill /f** — 不可跳过 `shutdown.bat` 直接 taskkill
- **端口检测用 socket** — `socket.create_connection(("127.0.0.1", port), timeout=...)`，不依赖进程存活判断
- **server.xml 用正则解析** — 不使用 XML 解析器（文件含有注释行和不一致格式），需跳过 `<!--` 开头行和 AJP connector 行
- **catalina.bat 调试端口搜索关键词 `Xdebug`** — 匹配 `address=192.168.151.77:(\d+)`，插入位置在第一个 `set CATALINA_OPTS=` 之后
- **gbk 编码解码 subprocess 输出** — `output.decode("gbk", errors="replace")`，Windows 中文环境特有
- **netstat 查端口加尾随空格** — `netstat -ano | findstr ":{port} "`（尾随空格防止子串误匹配）
- **资源管理器弹前台** — 用 `cmd /c start "" <path>` 而非直接 `explorer <path>`（pythonw.exe 下直接调用 explorer 会在后台打开）

### 前端

- **API 调用全走 `api/index.js`** — 组件不直接调 axios，新增接口在此文件加方法
- **`watch` + `v-if` 的 dialog 组件必须 `{ immediate: true }`** — 因为 `visible` prop 在组件挂载时已为 `true`
- **`sessionStorage` 缓存键名 `testhelper_envs`** — `App.vue` 用，格式不可变
- **`ElMessageBox.confirm` 用于停止操作** — 不可移除确认弹框
- **Version 点击复制环境信息** — 格式：`环境：{version}  访问地址：{access_url}  调试端口：{debug_port}`

## 编码规范

### Python

- 使用 `"""docstring"""` 为模块和函数写注释，说明目的而非实现方式
- 类型注解：函数参数和返回值标注类型
- 异常处理：尽量捕获具体异常类型（`FileNotFoundError`、`OSError`），避免裸露 `except:`
- 模块级常量用大写命名（`PORT_CHECK_TIMEOUT = 0.3`）
- 内部函数用下划线前缀（`_check_running`、`_get_connector_port`）

### Vue / JavaScript

- Vue 3 `<script setup>` 组合式 API，不使用 Options API
- 函数名用 `handle` 前缀处理用户操作（`handleStart`、`handleStop`）
- axios 响应拦截器中统一处理错误，组件只处理成功分支
- Element Plus 组件用中文语言包 `zhCn`
- 文件编码 UTF-8

## API 模式参考

```
GET    /api/envs                                   → list[dict]
POST   /api/envs/{version}/start                   → {"success": bool, "message": str}
POST   /api/envs/{version}/stop                    → {"success": bool, "message": str}
GET    /api/envs/{version}/props/{db|bi}           → dict[str, str] / {"error": "need_start"}
PUT    /api/envs/{version}/props/{db|bi}           → {"count": int, "backup": str}
PUT    /api/envs/{version}/props/{db|bi}/{key}     → {"key": str, "old_value": str, "new_value": str}
DELETE /api/envs/{version}/props/{db|bi}/{key}     → {"key": str, "deleted_value": str}
GET    /api/envs/{version}/server-ports            → {"shutdown_port": int, "connector_port": int}
PUT    /api/envs/{version}/server-ports            → {"shutdown_port": int, "connector_port": int}
GET    /api/envs/{version}/debug-port              → {"debug_port": int | null}
PUT    /api/envs/{version}/debug-port              → {"action": "added"|"modified", "debug_port": int}
DELETE /api/envs/{version}/debug-port              → {"success": True, "message": str}
```

路径中的 `{version}` 取值：`10.0`、`10.1`、`10.1.4.1`、`10.2`、`11.0`、`11.1`、`11.1Fabric`、`11.2`

## 目录结构

```
ENV_Manager/
├── CLAUDE.md                  ← 本文件
├── changeLog.log              ← 修改日志（每次代码修改追加记录）
├── config/
│   └── config.properties      # 系统运行参数（key=value 格式）
├── backend/
│   ├── app.py                 # Flask 路由注册
│   ├── config.py              # 路径常量 + 配置（从 config.properties 加载）
│   ├── requirements.txt       # pip 依赖
│   ├── tray_launcher.py       # 系统托盘启动
│   └── modules/
│       ├── config_properties.py # .properties 文件读写 + 转义
│       ├── env_discovery.py   # 环境扫描
│       ├── tomcat_ctl.py      # 启停控制
│       ├── props_editor.py    # properties CRUD
│       ├── server_xml.py      # server.xml 端口
│       └── catalina_editor.py # 调试端口
├── frontend/
│   ├── src/
│   │   ├── main.js            # Vue 入口
│   │   ├── App.vue            # 主页面
│   │   ├── api/index.js       # API 封装
│   │   └── components/
│   │       ├── PropsEditor.vue # properties 编辑器
│   │       └── PortEditor.vue # 端口编辑器
│   └── dist/                  # 构建产物
├── start.bat                  # 生产启动
├── start-dev.bat              # 开发启动
└── start-tray.bat             # 托盘启动
```

## 变更记录规范

每次对项目代码的修改（包括但不限于新增功能、修改逻辑、修复 Bug、重构、更新文档），必须执行以下两步：

### 1. 更新 `changeLog.log`

在文件末尾追加一行，格式如下：

```
[2026-05-27] [ADD] CLAUDE.md + changeLog.log — 添加项目规范文件和修改日志规则
```

| 标记 | 含义 |
|------|------|
| `ADD` | 新增功能或文件 |
| `MOD` | 修改已有逻辑 |
| `FIX` | 修复 Bug |
| `RM` | 删除功能或文件 |
| `DOC` | 仅文档相关修改 |

描述要求：简洁说明**改了什么 + 为什么**，让回溯时能快速理解上下文。

### 2. 同步更新 `README.md`

README.md 如有以下内容变更必须同步：
- 新增或修改了功能点
- API 接口有增减或变更
- 目录结构有变化
- 启动方式或依赖有变化
- 注意事项有新增

## 重要注意事项

- **端口 6688**：曾用 6666，因 Chrome 拦截 6665-6669 而更换，不可改回
- **前端修改后要 `npm run build`**：生产模式从 `dist/` 提供静态文件，如只改了前端源码必须重新构建
- **`db.properties` 首次启动前不存在**：API 返回 `{"error": "need_start"}`，前端显示提示消息而非空列表
- **启动黑窗**：`subprocess.Popen` 不捕获 `stdout/stderr`，让 Tomcat 控制台窗口正常显示
- **Windows 互斥体**：`tray_launcher.py` 用 `CreateMutexW` 防止重复启动
- **并行端口检测**：`ThreadPoolExecutor(max_workers=8, timeout=0.3)`，保持 8 个并发数和 0.3s 超时
