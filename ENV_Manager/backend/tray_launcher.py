"""
系统托盘启动器 — 后台运行 Waitress 服务 + 系统托盘图标。
使用 pythonw.exe 运行，无控制台窗口。

双击托盘图标 → 打开浏览器
右键托盘图标 → Quit
"""
import ctypes
import os
import sys
import threading
import webbrowser

import pystray
from PIL import Image, ImageDraw
from waitress import serve

# 确保能找到同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from config import API_PORT


def _create_icon_image():
    """生成 64x64 扳手图标。"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    body = (130, 130, 135, 255)
    shadow = (100, 100, 105, 255)

    # 梅花扳手头（环状）
    cx, cy = 32, 20
    draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=body)
    draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(0, 0, 0, 0))

    # 手柄
    draw.rectangle([cx - 5, cy - 2, cx + 5, cy + 36], fill=body)
    draw.rectangle([cx - 3, cy + 4, cx + 3, cy + 34], fill=shadow)

    # 手柄末端
    draw.rounded_rectangle([cx - 6, cy + 32, cx + 6, cy + 40], radius=3, fill=body)

    return img


def _start_server():
    """在后台线程启动 Waitress 服务。"""
    serve(app, host="127.0.0.1", port=API_PORT)


def _open_browser(icon):
    """双击托盘图标时打开浏览器。"""
    webbrowser.open(f"http://localhost:{API_PORT}")


def _quit_app(icon, item):
    """退出程序。"""
    icon.stop()
    os._exit(0)


def main():
    """启动入口：检测端口 → 注册路由 → 启动服务 → 托盘图标。"""
    # Windows 命名互斥体 — 防重复启动，由内核保证唯一性
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "ENV_Manager_Tray_Launcher")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        sys.exit(0)

    # 注册前端静态文件路由（生产模式）
    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "dist"
    )

    @app.route("/", defaults={"path": ""}, methods=["GET"])
    @app.route("/<path:path>", methods=["GET"])
    def serve_frontend(path):
        from flask import send_from_directory
        if path and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        return send_from_directory(frontend_dist, "index.html")

    # 启动 Waitress 服务（守护线程，随主线程退出而结束）
    server_thread = threading.Thread(target=_start_server, daemon=True)
    server_thread.start()

    # 创建系统托盘图标
    icon = pystray.Icon(
        "env_manager",
        _create_icon_image(),
        "ENV_Manager",
        menu=pystray.Menu(
            pystray.MenuItem("Quit", _quit_app),
        ),
    )
    icon._on_activate = _open_browser  # 双击响应
    icon.run()


if __name__ == "__main__":
    main()
