"""
环境发现模块 — 扫描 Environment 目录，获取所有 BI 系统实例列表。
新增扫描逻辑只需修改此文件。
"""
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from config import ENVIRONMENT_ROOT, get_server_xml
from modules.server_xml import read_server_ports

# 端口探测超时（秒）。本地检测毫秒级即可响应，无需长等待。
PORT_CHECK_TIMEOUT = 0.3


def discover_envs() -> list[dict]:
    """
    扫描 ENVIRONMENT_ROOT 下的所有子目录，返回环境信息列表。
    端口检测使用线程池并行执行以提高响应速度。
    """
    envs = []
    if not os.path.isdir(ENVIRONMENT_ROOT):
        return envs

    for entry in sorted(os.listdir(ENVIRONMENT_ROOT)):
        env_path = os.path.join(ENVIRONMENT_ROOT, entry)
        if not os.path.isdir(env_path):
            continue
        # 只识别包含 tomcat/bin 目录的实例
        tomcat_bin = os.path.join(env_path, "tomcat", "bin")
        if not os.path.isdir(tomcat_bin):
            continue

        info = {
            "version": entry,
            "status": "stopped",
            "connector_port": None,
            "shutdown_port": None,
        }

        # 读取 server.xml 中的端口信息
        try:
            ports = read_server_ports(get_server_xml(entry))
            info["connector_port"] = ports.get("connector_port")
            info["shutdown_port"] = ports.get("shutdown_port")
        except Exception:
            pass

        envs.append(info)

    # 并行检测端口状态（8 个环境串行需数秒，并行只需一次超时时间）
    with ThreadPoolExecutor(max_workers=8) as pool:
        for info in envs:
            if info["connector_port"]:
                pool.submit(_check_running, info)

    return envs


def _check_running(info: dict) -> None:
    """端口检测任务：若端口在监听则标记为 running。"""
    if is_port_listening(info["connector_port"]):
        info["status"] = "running"


def is_port_listening(port: int) -> bool:
    """检测指定端口是否处于监听状态。"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=PORT_CHECK_TIMEOUT):
            return True
    except (ConnectionRefusedError, OSError, socket.timeout):
        return False
