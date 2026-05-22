"""
server.xml 端口管理模块 — 读取和修改 Tomcat 的 Shutdown port 和 Connector port。
使用正则解析 XML，避免引入 XML 解析器对原始格式的干扰。
"""
import re


def read_server_ports(file_path: str) -> dict:
    """
    从 server.xml 中提取端口信息。
    返回 {"shutdown_port": int, "connector_port": int}。
    xml 里加了注释格式不同步的问题，所以使用正则解析。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    shutdown_port = None
    connector_port = None

    # 匹配 <Server port="9101" shutdown="SHUTDOWN">
    m = re.search(r'<Server\s+port="(\d+)"', content)
    if m:
        shutdown_port = int(m.group(1))

    # 匹配 <Connector port="8101" protocol="HTTP/1.1"
    # 排除注释行和 AJP connector
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("<!--") or stripped.startswith("-->"):
            continue
        if "AJP" in stripped:
            continue
        m = re.search(r'<Connector\s+port="(\d+)"', stripped)
        if m:
            connector_port = int(m.group(1))
            break

    return {
        "shutdown_port": shutdown_port,
        "connector_port": connector_port,
    }


def write_server_ports(file_path: str, shutdown_port: int, connector_port: int) -> None:
    """
    修改 server.xml 中的端口号，直接替换文件中的端口值。
    不改变 XML 的其他内容和格式。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换 Server port
    content = re.sub(
        r'(<Server\s+port=")(\d+)(")',
        lambda m: f'{m.group(1)}{shutdown_port}{m.group(3)}',
        content,
        count=1,
    )

    # 替换第一个非注释的 Connector port
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("<!--") or stripped.startswith("-->"):
            continue
        if "AJP" in stripped:
            continue
        if re.search(r'<Connector\s+port="\d+"', stripped):
            lines[i] = re.sub(
                r'(port=")(\d+)(")',
                lambda m: f'{m.group(1)}{connector_port}{m.group(3)}',
                line,
                count=1,
            )
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def build_access_url(connector_port: int) -> str:
    """根据 Connector port 拼接访问地址。"""
    return f"http://192.168.151.77:{connector_port}/bi/Viewer"
