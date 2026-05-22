"""
catalina.bat 调试端口管理模块 — 管理 JVM 调试端口（-Xrunjdwp）。
通过搜索 "Xdebug" 关键词定位调试配置行，支持增、改、删。
"""
import re


def read_debug_port(file_path: str) -> int | None:
    """
    读取调试端口号。搜索包含 "Xdebug" 的行并提取端口。
    未找到时返回 None。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    m = re.search(r"Xdebug.*address=192\.168\.151\.77:(\d+)", content)
    if m:
        return int(m.group(1))
    return None


def _has_debug_line(content: str) -> bool:
    """检查文件中是否存在调试配置行。"""
    return "Xdebug" in content


def _build_debug_line(port: int) -> str:
    """生成完整的调试配置行。"""
    return (
        f'set CATALINA_OPTS=%CATALINA_OPTS% -server -Xdebug -Xnoagent '
        f'-Djava.compiler=NONE -Xrunjdwp:transport=dt_socket,server=y,suspend=n,'
        f'address=192.168.151.77:{port}'
    )


def upsert_debug_port(file_path: str, port: int) -> dict:
    """
    新增或修改调试端口。
    若已有调试行 → 替换端口号；
    若无调试行 → 在第一个 set CATALINA_OPTS 后插入。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    debug_line = _build_debug_line(port) + "\n"
    new_lines = []
    first_catalina_found = False

    if _has_debug_line("".join(lines)):
        # 替换模式：找到调试行并替换端口号
        for line in lines:
            if "Xdebug" in line and "address=" in line:
                new_lines.append(
                    re.sub(
                        r"address=192\.168\.151\.77:\d+",
                        f"address=192.168.151.77:{port}",
                        line,
                    )
                )
            else:
                new_lines.append(line)
        action = "modified"
    else:
        # 新增模式：在第一个 set CATALINA_OPTS 后插入
        for line in lines:
            new_lines.append(line)
            if line.strip().startswith("set CATALINA_OPTS=") and not first_catalina_found:
                first_catalina_found = True
                new_lines.append(debug_line)
        action = "added"

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return {"action": action, "debug_port": port}


def delete_debug_port(file_path: str) -> dict:
    """
    删除调试端口配置行。
    搜索包含 "Xdebug" 和 "address=" 的行并移除。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = [line for line in lines if not ("Xdebug" in line and "address=" in line)]

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return {"success": True, "message": "调试端口配置已删除"}
