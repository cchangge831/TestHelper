# ENV_Manager — Project Overview for AI

## Project Purpose

A local web-based management tool for Yonghong BI systems on Windows. Manages 8 Java+Tomcat BI instances located at `C:\Users\cchan\Desktop\Environment\`. Provides start/stop, properties editing, port configuration, and debug port management through a web UI.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask + Waitress |
| Frontend | Vue 3 + Vite + Element Plus + Axios |
| Port | 6688 (Chrome blocks 6665-6669 as unsafe) |

## Directory Structure

```
ENV_Manager/
├── backend/
│   ├── app.py                    # Flask entry, all API routes
│   ├── config.py                 # Path constants, utility functions
│   ├── requirements.txt
│   └── modules/
│       ├── __init__.py
│       ├── env_discovery.py      # Scans Environment/ dir, parallel port detection
│       ├── tomcat_ctl.py         # start/stop via startup.bat + shutdown.bat + taskkill
│       ├── props_editor.py       # db.properties / bi.properties CRUD with .bak backup
│       ├── server_xml.py         # server.xml port read/write via regex
│       └── catalina_editor.py    # catalina.bat debug port management
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js               # Vue entry, Element Plus + zhCn locale
│       ├── App.vue               # Root component, env table
│       ├── api/index.js          # Axios wrapper, all API calls
│       └── components/
│           ├── PropsEditor.vue   # Key-value editor dialog for .properties files
│           └── PortEditor.vue    # Port + debug port editor (merged)
├── start.bat                     # Production: build frontend → start with waitress
├── start-dev.bat                 # Dev: Flask API + Vite dev server
├── README.md
└── README_FOR_AI.md              # This file
```

## Environment Structure (C:\Users\cchan\Desktop\Environment\)

```
{version}/
├── tomcat/
│   ├── bin/
│   │   ├── startup.bat           # Start script
│   │   ├── shutdown.bat          # Stop script
│   │   └── catalina.bat          # JVM args + debug port config
│   └── conf/
│       └── server.xml            # Shutdown port + Connector port
├── vividime/                     # 11.x versions (priority)
│   ├── db.properties
│   ├── bihome/bi.properties
│   └── product/                  # JAR directory
├── vividime/log/                 # Log files (11.x versions)
└── Yonghong/                     # 10.x versions (fallback)
    ├── db.properties
    ├── bihome/bi.properties
    └── product/
```

Versions: 10.0, 10.1, 10.1.4.1, 10.2, 11.0, 11.1, 11.1Fabric, 11.2

## Key Architecture Decisions

### 1. Backend (Flask, single-file routes)
- All API routes are in `app.py` — no blueprints, module is small enough
- `--serve-frontend` flag switches between dev (Flask dev server) and production (Waitress)
- Dev mode: `app.run(debug=True)` on `127.0.0.1:6688`
- Prod mode: `waitress.serve()` on `127.0.0.1:6688`, also serves `frontend/dist/` as static files
- CORS enabled via flask-cors for dev mode (frontend on port 5173)

### 2. Tomcat Control (tomcat_ctl.py)
- **Start**: `subprocess.Popen` fire-and-forget (no stdout/stderr capture, so the Tomcat black window appears normally). Polls port every 2s × 6 = 12s timeout.
- **Stop**: Two-phase: (1) `shutdown.bat` graceful, wait 3s; (2) if port still listening, `netstat -ano | findstr :{port}` to get PID → `taskkill /f /pid`
- Status detection via socket `create_connection` on `127.0.0.1:{connector_port}`

### 3. Environment Discovery (env_discovery.py)
- Scans `ENVIRONMENT_ROOT` for subdirectories containing `tomcat/bin/`
- Reads ports from `server.xml` via `read_server_ports()`
- Checks running status via parallel socket probes (`ThreadPoolExecutor max_workers=8`, 0.3s timeout each)
- Frontend caches results in `sessionStorage` (key: `testhelper_envs`)

### 4. Properties Editor (props_editor.py)
- File lookup priority: `vividime/` → `vividime/bihome/` → `Yonghong/` → `Yonghong/bihome/`
- Save creates `.bak` backup before writing
- `db.properties` may not exist before first system launch — API returns `{"error": "need_start"}`

### 5. Server XML (server_xml.py)
- Regex-based parsing/editing (avoids XML parser issues with comments/inconsistent formatting)
- Replaces `<Server port="N">` for shutdown port, first non-comment `<Connector port="N">` for connector port

### 6. Debug Port (catalina_editor.py)
- Searches for `Xdebug.*address=192.168.151.77:(\d+)` in catalina.bat
- Supports add (after first `set CATALINA_OPTS=`), modify (replace port number), delete (remove line)

### 7. Frontend (Vue 3 + Element Plus)
- Single page, `el-table` listing environments with action buttons
- Action buttons per environment: Start, Stop, Access, Jar, **Log**
- PropsEditor: `el-dialog` 850px wide, 90vh max-height with scrollable table, inline editing
- PortEditor: merged Tomcat ports + debug port in one dialog, `el-input type="number"` (no +/- buttons)
- `App.vue` watches use `{ immediate: true }` because components are `v-if` rendered
- Stop action uses `ElMessageBox.confirm` before sending request
- Clicking port number copies formatted env info to clipboard (version + URL + debug port)

### 8. Explorer Window Foreground (`_open_explorer`)
- Helper function in `app.py` that opens a folder in Windows Explorer and brings it to foreground
- Uses `cmd /c start "" <path>` instead of direct `explorer <path>` call
- `start` command forces the new explorer window to pop to the front, unlike raw `explorer.exe`
- Used by both Jar (`open-jar`) and Log (`open-log`) endpoints

## API Reference

### Environment
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/envs` | List all environments with status |
| POST | `/api/envs/{version}/start` | Start Tomcat |
| POST | `/api/envs/{version}/stop` | Stop Tomcat (graceful + force) |
| GET | `/api/envs/{version}/access-url` | Get BI access URL |
| POST | `/api/envs/{version}/open-jar` | Open JAR folder in Explorer (foreground) |
| POST | `/api/envs/{version}/open-log` | Open log folder in Explorer (foreground) |

### Properties
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/envs/{version}/props/{file}` | Get all key-value pairs (`db` or `bi`) |
| PUT | `/api/envs/{version}/props/{file}` | Batch save (full overwrite, auto `.bak`) |
| PUT | `/api/envs/{version}/props/{file}/{key}` | Update single key |
| DELETE | `/api/envs/{version}/props/{file}/{key}` | Delete key |

### Ports
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/envs/{version}/server-ports` | Get `shutdown_port` + `connector_port` |
| PUT | `/api/envs/{version}/server-ports` | Update ports |
| GET | `/api/envs/{version}/debug-port` | Get debug port (or null) |
| PUT | `/api/envs/{version}/debug-port` | Create/update debug port |
| DELETE | `/api/envs/{version}/debug-port` | Remove debug port config |

## Important Notes for AI

- **Port 6688**: Originally 6666, changed because Chrome blocks 6665-6669
- **Windows-specific**: netstat parsing, taskkill, explorer.exe, os.startfile — all Windows-only
- **Encoding**: `subprocess` output decoded with `gbk` (Windows Chinese locale)
- **Batch file cwd**: startup.bat/shutdown.bat MUST run with `cwd=script_dir` or they fail
- **startup.bat behavior**: Uses `start` command, parent script exits immediately. Don't check process liveness — check port instead
- **netstat parsing**: `netstat -ano | findstr ":{port} "` — note trailing space to avoid substring matches
- **server.xml**: Has inline comments, some lines start with `<!--`. Regex skips comment lines and AJP connector lines
- **catalina.bat**: May or may not have debug port line. If absent, insert after first `set CATALINA_OPTS=`
- **Frontend watch + v-if**: When using `v-if` to show dialogs, the watcher on `props.visible` needs `{ immediate: true }` because the prop is already `true` when the component mounts
- **Dist files**: After editing frontend source, run `npm run build` in `frontend/` to regenerate `dist/`
- **Production server**: Uses Waitress, not Flask's built-in server. Flask dev server is only for development mode (without `--serve-frontend`)
- **Explorer foreground**: `subprocess.Popen(["explorer", path])` opens in background when called from pythonw.exe. Use `cmd /c start "" <path>` to force foreground

### 9. System Tray Mode (tray_launcher.py)
- New entry point `tray_launcher.py` designed to run with `pythonw.exe` (no console window)
- Uses `pystray` + `Pillow` for system tray icon (wrench icon generated programmatically)
- **Double-click** tray icon → opens browser to http://localhost:6688
- **Right-click** → only "Quit" option, exits the process
- Waitress server runs in a daemon thread; tray icon runs on main thread
- Launched via `start-tray.bat` or desktop `C:\Users\cchan\Desktop\ENV_Manager.bat` (brief console for build, then closes)
- `pythonw.exe` creates no console window of its own
- Dependencies: `pystray`, `Pillow` (added to requirements.txt)

## Running

```bash
# Development (two servers, hot-reload)
start-dev.bat
# → Backend: http://localhost:6688, Frontend: http://localhost:5173

# Production — single server, needs build (has console window)
start.bat
# → http://localhost:6688

# Production — system tray mode, no console window (recommended for daily use)
start-tray.bat
# → Briefly shows console for build, then tray icon appears
# → Double-click tray icon: http://localhost:6688
# → Right-click tray icon: Quit
```

Desktop shortcut: `C:\Users\cchan\Desktop\ENV_Manager.bat`
