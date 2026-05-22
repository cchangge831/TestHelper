"""
Flask 主入口 — 注册所有 API 路由，启动服务。
支持 --serve-frontend 参数在生产模式下托管前端静态文件。
"""
import argparse
import os
import subprocess
import sys

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from config import (
    API_PORT, get_server_xml, get_catalina_bat,
    find_props_file, find_product_dir, find_log_dir,
)
from modules.env_discovery import discover_envs
from modules.tomcat_ctl import start_tomcat, stop_tomcat
from modules.server_xml import read_server_ports, write_server_ports, build_access_url
from modules.props_editor import read_props, update_prop, delete_prop, write_props_batch
from modules.catalina_editor import read_debug_port, upsert_debug_port, delete_debug_port

app = Flask(__name__)
CORS(app)

# 前端构建产物的目录（生产模式下使用）
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


# ===================== 环境管理 =====================

@app.route("/api/envs", methods=["GET"])
def api_list_envs():
    """获取所有环境列表及运行状态。"""
    envs = discover_envs()
    return jsonify(envs)


@app.route("/api/envs/<version>/start", methods=["POST"])
def api_start_env(version):
    """启动指定版本环境。"""
    result = start_tomcat(version)
    return jsonify(result), 200 if result["success"] else 500


@app.route("/api/envs/<version>/stop", methods=["POST"])
def api_stop_env(version):
    """停止指定版本环境。"""
    result = stop_tomcat(version)
    return jsonify(result), 200 if result["success"] else 500


@app.route("/api/envs/<version>/access-url", methods=["GET"])
def api_access_url(version):
    """获取环境的访问地址。"""
    ports = read_server_ports(get_server_xml(version))
    if ports.get("connector_port"):
        url = build_access_url(ports["connector_port"])
        return jsonify({"url": url})
    return jsonify({"error": "未找到 Connector port"}), 404


@app.route("/api/envs/<version>/jar-path", methods=["GET"])
def api_jar_path(version):
    """获取 jar 包目录路径。"""
    path = find_product_dir(version)
    if path:
        return jsonify({"path": path})
    return jsonify({"error": "未找到 product 目录"}), 404


def _open_explorer(path: str) -> None:
    """在资源管理器中打开路径并弹到前台。"""
    subprocess.Popen(["cmd", "/c", "start", "", path])


@app.route("/api/envs/<version>/open-jar", methods=["POST"])
def api_open_jar(version):
    """在 Windows 资源管理器中打开 jar 包目录。"""
    path = find_product_dir(version)
    if not path:
        return jsonify({"error": "未找到 product 目录"}), 404
    _open_explorer(path)
    return jsonify({"success": True, "path": path})


@app.route("/api/envs/<version>/open-log", methods=["POST"])
def api_open_log(version):
    """在 Windows 资源管理器中打开日志目录。"""
    path = find_log_dir(version)
    if not path:
        return jsonify({"error": "未找到 log 目录"}), 404
    _open_explorer(path)
    return jsonify({"success": True, "path": path})


# ===================== Properties CRUD =====================

def _resolve_props_file(version: str, file_key: str) -> tuple[str | None, str]:
    """
    根据 file_key（db 或 bi）查找对应的 properties 文件路径。
    返回 (file_path, display_name)。
    db.properties 不存在时返回特定错误标识。
    """
    filename_map = {"db": "db.properties", "bi": "bi.properties"}
    filename = filename_map.get(file_key)
    if not filename:
        return None, f"未知文件类型: {file_key}"

    file_path = find_props_file(version, filename)
    return file_path, filename


@app.route("/api/envs/<version>/props/<file_key>", methods=["GET"])
def api_list_props(version, file_key):
    """获取 properties 文件的所有键值对。"""
    file_path, filename = _resolve_props_file(version, file_key)
    if not file_path:
        if filename == "db.properties":
            return jsonify({"error": "need_start", "message": "db.properties 不存在，需要启动系统来创建"}), 404
        return jsonify({"error": f"{filename} 不存在"}), 404
    props = read_props(file_path)
    return jsonify(props)


@app.route("/api/envs/<version>/props/<file_key>", methods=["PUT"])
def api_batch_save_props(version, file_key):
    """批量保存全部键值对（全量覆盖），触发一次备份。"""
    file_path, filename = _resolve_props_file(version, file_key)
    if not file_path:
        return jsonify({"error": f"{filename} 不存在"}), 404
    data = request.get_json()
    result = write_props_batch(file_path, data)
    return jsonify(result)


@app.route("/api/envs/<version>/props/<file_key>/<prop_key>", methods=["PUT"])
def api_update_prop(version, file_key, prop_key):
    """更新指定 key 的值，若不存在则新增。"""
    file_path, filename = _resolve_props_file(version, file_key)
    if not file_path:
        return jsonify({"error": f"{filename} 不存在"}), 404
    data = request.get_json()
    value = data.get("value", "")
    result = update_prop(file_path, prop_key, value)
    return jsonify(result)


@app.route("/api/envs/<version>/props/<file_key>/<prop_key>", methods=["DELETE"])
def api_delete_prop(version, file_key, prop_key):
    """删除指定 key。"""
    file_path, filename = _resolve_props_file(version, file_key)
    if not file_path:
        return jsonify({"error": f"{filename} 不存在"}), 404
    result = delete_prop(file_path, prop_key)
    return jsonify(result)


# ===================== server.xml 端口 =====================

@app.route("/api/envs/<version>/server-ports", methods=["GET"])
def api_get_server_ports(version):
    """获取 Shutdown port 和 Connector port。"""
    ports = read_server_ports(get_server_xml(version))
    return jsonify(ports)


@app.route("/api/envs/<version>/server-ports", methods=["PUT"])
def api_update_server_ports(version):
    """修改 Shutdown port 和 Connector port。"""
    data = request.get_json()
    shutdown_port = data.get("shutdown_port")
    connector_port = data.get("connector_port")
    if not shutdown_port or not connector_port:
        return jsonify({"error": "请提供 shutdown_port 和 connector_port"}), 400
    write_server_ports(get_server_xml(version), shutdown_port, connector_port)
    return jsonify({"shutdown_port": shutdown_port, "connector_port": connector_port})


# ===================== catalina.bat 调试端口 =====================

@app.route("/api/envs/<version>/debug-port", methods=["GET"])
def api_get_debug_port(version):
    """获取调试端口号，无则返回 null。"""
    port = read_debug_port(get_catalina_bat(version))
    return jsonify({"debug_port": port})


@app.route("/api/envs/<version>/debug-port", methods=["PUT"])
def api_upsert_debug_port(version):
    """新增或修改调试端口。"""
    data = request.get_json()
    port = data.get("debug_port")
    if not port or not isinstance(port, int):
        return jsonify({"error": "请提供有效的 debug_port"}), 400
    result = upsert_debug_port(get_catalina_bat(version), port)
    return jsonify(result)


@app.route("/api/envs/<version>/debug-port", methods=["DELETE"])
def api_delete_debug_port(version):
    """删除调试端口配置。"""
    result = delete_debug_port(get_catalina_bat(version))
    return jsonify(result)


# ===================== 入口 =====================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BI 系统管理工具")
    parser.add_argument(
        "--serve-frontend",
        action="store_true",
        help="生产模式：同时托管前端静态文件（需先 npm run build）",
    )
    args = parser.parse_args()

    if args.serve_frontend:
        # 生产模式：注册静态文件路由，使用 waitress 生产级服务器
        @app.route("/", defaults={"path": ""}, methods=["GET"])
        @app.route("/<path:path>", methods=["GET"])
        def serve_frontend(path):
            if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
                return send_from_directory(FRONTEND_DIST, path)
            return send_from_directory(FRONTEND_DIST, "index.html")

        from waitress import serve
        print(f"ENV_Manager 服务启动于 http://localhost:{API_PORT}")
        serve(app, host="127.0.0.1", port=API_PORT)
    else:
        # 开发模式：使用 Flask 内置服务器（带热更新）
        print(f"ENV_Manager API 服务启动于 http://localhost:{API_PORT}")
        app.run(host="127.0.0.1", port=API_PORT, debug=True)
