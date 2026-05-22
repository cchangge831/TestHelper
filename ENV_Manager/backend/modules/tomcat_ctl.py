"""
Tomcat 启停控制模块 — 直接调用 startup.bat / shutdown.bat。
启动后等待 3 秒检测端口是否监听，失败则返回脚本错误输出。
"""
import os
import socket
import subprocess
import time
from config import get_startup_script, get_shutdown_script, get_server_xml
from modules.server_xml import read_server_ports


def _get_connector_port(version: str) -> int | None:
    """从 server.xml 读取 Connector 端口号。"""
    try:
        ports = read_server_ports(get_server_xml(version))
        return ports.get("connector_port")
    except Exception:
        return None


def _port_listening(port: int) -> bool:
    """检测端口是否处于监听状态。"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except Exception:
        return False


def _find_pid_by_port(port: int) -> int | None:
    """通过 netstat 查找占用指定端口的进程 PID。"""
    try:
        output = subprocess.check_output(
            f'netstat -ano | findstr ":{port} "',
            shell=True, stderr=subprocess.STDOUT, timeout=5,
        ).decode("gbk", errors="replace")
        for line in output.splitlines():
            if "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid.isdigit():
                    return int(pid)
    except Exception:
        pass
    return None


def start_tomcat(version: str) -> dict:
    """
    执行 startup.bat 启动 Tomcat。
    不捕获输出（黑窗正常显示），等待数秒后通过端口检测确认启动状态。
    startup.bat 通过 start 命令启动 Java 进程后会立即退出，不依赖进程存活判断。
    """
    script = get_startup_script(version)
    if not os.path.isfile(script):
        return {"success": False, "message": f"启动脚本不存在: {script}"}

    script_dir = os.path.dirname(script)
    port = _get_connector_port(version)

    try:
        # 不捕获输出 → 黑窗正常显示，等同于用户双击 startup.bat
        subprocess.Popen([script], cwd=script_dir, shell=True)

        # 等待 Tomcat 初始化（端口开始监听）
        for _ in range(6):
            time.sleep(2)
            if port and _port_listening(port):
                return {"success": True,
                        "message": f"{version} 启动成功（端口 {port} 已监听）"}

        if port:
            return {"success": True,
                    "message": f"{version} 启动命令已执行，但端口 {port} 尚未监听，请稍后检查"}
        return {"success": True,
                "message": f"{version} 启动命令已执行"}

    except Exception as e:
        return {"success": False, "message": f"启动异常: {str(e)}"}


def stop_tomcat(version: str) -> dict:
    """
    停止指定版本的 Tomcat。
    先试 shutdown.bat 优雅关闭，若端口仍在监听则通过 netstat + taskkill 强制杀进程。
    """
    port = _get_connector_port(version)
    if not port:
        return {"success": False, "message": f"无法获取 {version} 的端口号"}

    # 1) 先试 shutdown.bat 优雅关闭
    script = get_shutdown_script(version)
    if os.path.isfile(script):
        try:
            subprocess.run(
                [script],
                cwd=os.path.dirname(script),
                shell=True, timeout=5,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    # 等 3 秒看端口是否已释放
    time.sleep(3)
    if not _port_listening(port):
        return {"success": True, "message": f"{version} 已停止"}

    # 2) 端口仍在监听 → 通过端口查 PID 强制 kill
    pid = _find_pid_by_port(port)
    if pid:
        try:
            subprocess.run(
                ["taskkill", "/f", "/pid", str(pid)],
                capture_output=True, timeout=5,
            )
        except Exception:
            pass

    # 最终确认
    time.sleep(1)
    if _port_listening(port):
        return {"success": False, "message": f"{version} 无法停止，请手动关闭 Tomcat 黑窗"}

    return {"success": True, "message": f"{version} 已停止"}
