"""
配置模块 — 从 config/config.properties 读取运行时参数，缺项用硬编码默认值。
敏感信息（如 API Key）从环境变量读取。
"""

import os
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent / "config"
CONFIG_FILE = CONFIG_DIR / "config.properties"

# ==================== 默认值 ====================
_DEFAULTS = {
    "qwen_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "qwen_vision_model": "qwen-vl-max",
    "qwen_timeout": "60",
    "browser_type": "chromium",
    "chrome_debug_port": "9222",
    "browser_timeout": "30000",
    "browser_headless": "false",
}

_config_cache: dict[str, str] = {}


def _unescape(value: str) -> str:
    """将 properties 转义还原"""
    value = value.replace(r"\=", "=")
    value = value.replace(r"\#", "#")
    value = value.replace(r"\\", "\\")
    return value


def _load_config() -> dict[str, str]:
    """读取 config.properties，返回合并后的配置字典"""
    config = dict(_DEFAULTS)
    if not CONFIG_FILE.exists():
        return config
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            eq_pos = stripped.index("=")
            key = stripped[:eq_pos].strip()
            value = stripped[eq_pos + 1:].strip()
            if key:
                config[key] = _unescape(value)
    return config


def _get(key: str) -> str:
    """获取配置项"""
    global _config_cache
    if not _config_cache:
        _config_cache = _load_config()
    return _config_cache.get(key, _DEFAULTS.get(key, ""))


# ==================== 便捷访问函数 ====================

def get_str(key: str) -> str:
    return _get(key)


def get_int(key: str) -> int:
    return int(_get(key))


def get_bool(key: str) -> bool:
    return _get(key).lower() == "true"


def qwen_api_key() -> str:
    """从环境变量 QWEN_API_KEY 读取 API Key（不写入配置文件）"""
    return os.environ.get("QWEN_API_KEY", "")


def qwen_base_url() -> str:
    return _get("qwen_base_url")


def qwen_vision_model() -> str:
    return _get("qwen_vision_model")


def qwen_timeout() -> int:
    return int(_get("qwen_timeout"))


def browser_type() -> str:
    return _get("browser_type")


def chrome_debug_port() -> int:
    return int(_get("chrome_debug_port"))


def browser_timeout() -> int:
    return int(_get("browser_timeout"))


def browser_headless() -> bool:
    return _get("browser_headless").lower() == "true"
