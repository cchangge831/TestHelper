"""
系统配置文件读写模块 — 按 Java .properties 格式处理 key=value 键值对。
支持路径中的反斜杠、特殊符号等转义规则。
"""
import os


def read_config(file_path: str) -> dict:
    """
    读取 .properties 文件，返回有序键值对字典。
    转义规则：
      \\ → \
      \\= → =  (行中)
      \\# → #  (行首)
      \\n → 换行
    """
    props = {}
    if not os.path.isfile(file_path):
        return props

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    buf = ""
    i = 0
    n = len(content)
    while i < n:
        ch = content[i]
        if ch == "\\" and i + 1 < n and content[i + 1] in {"\\", "=", "#", "n"}:
            next_ch = content[i + 1]
            if next_ch == "n":
                buf += "\n"
            else:
                buf += next_ch
            i += 2
        else:
            buf += ch
            i += 1

    for line in buf.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            props[key.strip()] = value.strip()

    return props


def write_config(file_path: str, props: dict) -> None:
    """
    将键值对写入 .properties 文件（全量覆盖）。
    自动处理转义：
      \\ → \\\\
      = → \\=  (仅对 key)
      key 或 value 中行首的 # → \\#
    """
    lines = []
    lines.append("# ENV_Manager 系统配置文件")
    lines.append("")
    for key, value in props.items():
        key_esc = _escape_key(key)
        value_esc = _escape_value(value)
        lines.append(f"{key_esc}={value_esc}")

    # 确保目录存在
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def get_config_value(file_path: str, key: str, default: str | None = None) -> str | None:
    """读取单个配置项，找不到返回 default。"""
    props = read_config(file_path)
    return props.get(key, default)


def set_config_value(file_path: str, key: str, value: str) -> None:
    """设置单个配置项并写回文件。"""
    props = read_config(file_path)
    props[key] = value
    write_config(file_path, props)


def _escape_key(key: str) -> str:
    """转义 key 中的特殊字符。"""
    result = key.replace("\\", "\\\\")
    result = result.replace("=", "\\=")
    if result.startswith("#"):
        result = "\\" + result
    return result


def _escape_value(value: str) -> str:
    """转义 value 中的特殊字符（主要是反斜杠，如 Windows 路径）。"""
    result = value.replace("\\", "\\\\")
    if result.startswith("#"):
        result = "\\" + result
    return result
