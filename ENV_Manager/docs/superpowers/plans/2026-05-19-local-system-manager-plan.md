# BI 系统管理工具 Implementation Plan

> **Status:** ✅ COMPLETED — All tasks implemented.

**Goal:** 构建一个基于 Flask + Vue 3 的本地 Web 管理工具，管理 Windows 上多个 Java+Tomcat BI 系统的启停和配置。

**Architecture:** 前后端分离，Flask 提供 RESTful API，Vue 3 + Element Plus 实现管理界面。支持开发模式（双服务热更新）和生产模式（单服务 Waitress 部署）。

**Tech Stack:** Python 3 + Flask + Waitress, Vue 3 + Vite + Element Plus + Axios

---

### Task 1: 后端项目骨架 ✅

**Files:**
- Create: `backend/requirements.txt` ✅
- Create: `backend/config.py` ✅
- Create: `backend/modules/__init__.py` ✅

### Task 2: 环境发现模块 ✅

**Files:**
- Create: `backend/modules/env_discovery.py` ✅

**Deviation:** 最终实现使用 `ThreadPoolExecutor(max_workers=8)` 并行端口检测，`PORT_CHECK_TIMEOUT=0.3`，而非原始计划中的顺序检测。

### Task 3: Tomcat 启停控制模块 ✅

**Files:**
- Create: `backend/modules/tomcat_ctl.py` ✅

**Deviation from plan:**
- **启动**：不使用 `CREATE_NEW_CONSOLE`，改为 `subprocess.Popen` fire-and-forget 不捕获输出，黑窗正常显示。启动后轮询端口检测（每 2 秒 × 6 次 = 12 秒超时）。
- **停止**：原始计划只执行 `shutdown.bat`。最终实现为两步策略 — 先 `shutdown.bat` 等待 3 秒，若端口仍在监听则通过 `netstat -ano | findstr` 查 PID → `taskkill /f /pid` 强制杀。

### Task 4: server.xml 端口读写模块 ✅

**Files:**
- Create: `backend/modules/server_xml.py` ✅

### Task 5: properties 文件 CRUD 模块 ✅

**Files:**
- Create: `backend/modules/props_editor.py` ✅

### Task 6: catalina.bat 调试端口管理模块 ✅

**Files:**
- Create: `backend/modules/catalina_editor.py` ✅

### Task 7: Flask 主入口与 API 路由 ✅

**Files:**
- Create: `backend/app.py` ✅

**Deviation:** 生产模式使用 `waitress.serve()` 代替 Flask 内置服务器。不再使用 `webbrowser.open()`。不再在开发模式手动移除静态文件路由（改为条件注册）。

### Task 8: 前端项目初始化 ✅

**Files:**
- Create: `frontend/package.json` ✅
- Create: `frontend/vite.config.js` ✅
- Create: `frontend/index.html` ✅
- Create: `frontend/src/main.js` ✅

### Task 9: 前端 API 层 ✅

**Files:**
- Create: `frontend/src/api/index.js` ✅

**Deviation:** 移除了 `frontend/src/utils/message.js`（直接在组件内使用 ElMessage）。

### Task 10: 前端主页面 — 环境列表表格 ✅

**Files:**
- Create: `frontend/src/App.vue` ✅

**Deviation from plan:**
- 地址列改为可点击的端口按钮，点击复制环境信息到剪贴板（含版本、访问地址、调试端口）
- 移除"调试"配置按钮（调试端口合并到端口编辑器中）
- 增加 `sessionStorage` 缓存机制，页面加载时先展示缓存数据再后台刷新
- 停止按钮增加 `ElMessageBox.confirm` 二次确认

### Task 11: Properties 编辑器组件 ✅

**Files:**
- Create: `frontend/src/components/PropsEditor.vue` ✅

**Deviation:** 对话框宽度从 700px 改为 850px，增加 `top="3vh"`，表格 `max-height="500"` 改为 `:max-height="tableMaxHeight"`（`calc(90vh - 180px)`），去除等宽字体样式使用系统字体，watch 增加 `{ immediate: true }`。

### Task 12: 端口编辑器组件 ✅

**Files:**
- Create: `frontend/src/components/PortEditor.vue` ✅

**Deviation from plan:**
- 合并了调试端口管理（原 DebugPortEditor 不再独立存在）
- `el-input-number` 改为 `el-input type="number" v-model.number`（无 +/- 按钮）
- 移除了访问地址展示和复制按钮
- 新增调试端口字段、删除调试端口按钮
- watch 增加 `{ immediate: true }`

### Task 13: 调试端口编辑器组件 ✅

**Files:**
- Create: `frontend/src/components/DebugPortEditor.vue` — 已合并到 PortEditor.vue，此文件未创建

### Task 14: 启动脚本与桌面快捷方式 ✅

**Files:**
- Create: `start-dev.bat` ✅
- Create: `start.bat` ✅

**Deviation:** 后端端口改为 6688（Chrome 将 6666 列为不安全端口）。

---

## 实现偏差总结

| 项目 | 计划 | 实际 |
|------|------|------|
| 服务端口 | 6666 | 6688（Chrome ERR_UNSAFE_PORT） |
| 停止策略 | shutdown.bat | shutdown.bat + taskkill 兜底 |
| 启动策略 | CREATE_NEW_CONSOLE | fire-and-forget + 端口轮询 |
| 端口检测 | 顺序 1s 超时 | 并行线程池 0.3s 超时 |
| 生产服务器 | Flask 内置 | Waitress |
| 前端缓存 | 无 | sessionStorage |
| DebugPortEditor | 独立组件 | 合并到 PortEditor |
| PropsEditor 样式 | 700px 等宽字体 | 850px 系统字体 90vh |
