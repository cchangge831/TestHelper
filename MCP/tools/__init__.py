"""
工具注册中心 — 汇总所有工具模块的 TOOLS 定义和处理函数。

新增工具的步骤：
1. 在 tools/ 下创建 new_feature.py
2. 该模块需导出：TOOLS (list[dict]) 和 handle_tool(name, arguments) 函数
3. 在本文件 import 该模块，加入 _MODULES 列表

无需修改 server.py，工具自动生效。
"""

from tools import image_analyzer, browser_ctl, chat_hook

# 按顺序注册工具模块（导入顺序即工具列表中的展示顺序）
_MODULES = [
    chat_hook,
    image_analyzer,
    browser_ctl,
]


def get_all_tools() -> list[dict]:
    """汇总所有模块的 TOOLS 定义"""
    all_tools = []
    for mod in _MODULES:
        if hasattr(mod, "TOOLS"):
            all_tools.extend(mod.TOOLS)
    return all_tools


async def handle_tool(name: str, arguments: dict) -> list:
    """路由工具调用到对应模块"""
    for mod in _MODULES:
        if hasattr(mod, "handle_tool"):
            result = await mod.handle_tool(name, arguments)
            # 如果返回 None 表示该模块不认识此工具，继续尝试下一个
            if result is not None:
                return result
    return [{"type": "text", "text": f"未知工具: {name}"}]
