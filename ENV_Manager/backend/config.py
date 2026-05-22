"""
配置文件 — 集中管理路径常量与各模块共用工具函数。
修改 ENVIRONMENT_ROOT 可指向不同的环境根目录。
"""
import os

# ============================================================
# 环境根目录（修改此路径可切换管理范围）
# ============================================================
ENVIRONMENT_ROOT = r"C:\Users\cchan\Desktop\Environment"

# ============================================================
# API 服务配置
# ============================================================
API_PORT = 6688

# ============================================================
# 路径查找工具函数
# ============================================================


def get_env_path(version: str) -> str:
    """获取指定版本环境的绝对路径。"""
    return os.path.join(ENVIRONMENT_ROOT, version)


def get_startup_script(version: str) -> str:
    """获取 startup.bat 完整路径。"""
    return os.path.join(get_env_path(version), "tomcat", "bin", "startup.bat")


def get_shutdown_script(version: str) -> str:
    """获取 shutdown.bat 完整路径。"""
    return os.path.join(get_env_path(version), "tomcat", "bin", "shutdown.bat")


def get_server_xml(version: str) -> str:
    """获取 server.xml 完整路径。"""
    return os.path.join(get_env_path(version), "tomcat", "conf", "server.xml")


def get_catalina_bat(version: str) -> str:
    """获取 catalina.bat 完整路径。"""
    return os.path.join(get_env_path(version), "tomcat", "bin", "catalina.bat")


def find_props_file(version: str, filename: str) -> str | None:
    """
    在环境目录下查找 properties 文件。
    搜索优先级：vividime/ → Yonghong/
    返回完整路径，未找到则返回 None。
    """
    env_path = get_env_path(version)
    candidates = [
        os.path.join(env_path, "vividime", filename),
        os.path.join(env_path, "vividime", "bihome", filename),
        os.path.join(env_path, "Yonghong", filename),
        os.path.join(env_path, "Yonghong", "bihome", filename),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def find_product_dir(version: str) -> str | None:
    """查找 jar 包目录：vividime/product → Yonghong/product。"""
    env_path = get_env_path(version)
    candidates = [
        os.path.join(env_path, "vividime", "product"),
        os.path.join(env_path, "Yonghong", "product"),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return None


def find_log_dir(version: str) -> str | None:
    """查找日志目录：vividime/log → Yonghong/log。"""
    env_path = get_env_path(version)
    candidates = [
        os.path.join(env_path, "vividime", "log"),
        os.path.join(env_path, "Yonghong", "log"),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return None
