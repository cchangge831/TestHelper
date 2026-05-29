"""
聊天钩子工具 — 处理用户消息中的图片，调用识图模型分析后返回文本描述。

支持三种输入方式：
1. image_path：指定本地图片文件路径
2. image_base64：直接传入图片的 base64 编码
3. auto_scan：自动扫描 image_temp/ 目录中的最新图片
"""

from pathlib import Path
from typing import Any

from tools.image_analyzer import _analyze_image

# image_temp 目录路径
_IMAGE_TEMP_DIR = Path(__file__).resolve().parent.parent / "image_temp"

# ==================== 工具定义 ====================

TOOLS = [
    {
        "name": "process_chat",
        "description": (
            "【聊天图片钩子】处理用户消息中的图片。"
            "当用户发送图片且主模型无法直接查看时，调用此工具。"
            "支持三种输入模式："
            "1. image_path：指定图片文件路径"
            "2. image_base64：直接传入图片的 base64 编码"
            "3. auto_scan：自动从 image_temp/ 目录找到最新图片"
            "内部自动调用识图模型，返回「图片内容描述 + 用户文字」的组合文本。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件的绝对路径。与 image_base64/auto_scan 三选一。",
                },
                "image_base64": {
                    "type": "string",
                    "description": "图片的 base64 编码（不含 data:image 前缀）。与 image_path/auto_scan 三选一。",
                },
                "auto_scan": {
                    "type": "boolean",
                    "description": "自动扫描 image_temp/ 目录，使用其中最新的图片文件。与 image_path/image_base64 三选一。",
                    "default": False,
                },
                "user_text": {
                    "type": "string",
                    "description": "用户随图片发送的文字内容。",
                },
                "question": {
                    "type": "string",
                    "description": "针对图片的具体问题，如 '图中有什么错误？'。不传则返回通用描述。",
                },
            },
            "required": [],
        },
    },
]

# ==================== 处理函数 ====================


async def handle_tool(name: str, arguments: dict[str, Any]) -> list:
    """路由工具调用"""
    if name == "process_chat":
        return await _process_chat(arguments)
    return None


def _find_latest_image() -> str | None:
    """在 image_temp/ 目录中找到最新的图片文件"""
    if not _IMAGE_TEMP_DIR.exists():
        return None

    extensions = ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.bmp")
    files = []
    for ext in extensions:
        files.extend(_IMAGE_TEMP_DIR.glob(ext))

    if not files:
        return None

    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return str(files[0])


async def _process_chat(args: dict[str, Any]) -> list:
    """处理用户输入：先识别图片，再组合返回"""
    image_path = args.get("image_path", "").strip()
    image_base64 = args.get("image_base64", "").strip()
    auto_scan = args.get("auto_scan", False)
    user_text = args.get("user_text", "").strip()
    question = args.get("question", "").strip()

    # 1. 确定图片来源（优先级：image_path > image_base64 > auto_scan）
    if not image_path and not image_base64 and auto_scan:
        image_path = _find_latest_image()
        if not image_path:
            return [{"type": "text", "text": (
                "错误：auto_scan 开启但 image_temp/ 目录中没有图片文件。\n"
                "请先将图片保存到 image_temp/ 目录下。"
            )}]

    if not image_path and not image_base64:
        return [{"type": "text", "text": (
            "错误：未指定图片。请提供 image_path、image_base64，或设置 auto_scan=true。"
        )}]

    # 2. 调用识图工具获取图片描述
    analyze_args = {}
    if image_base64:
        analyze_args["image_base64"] = image_base64
    else:
        analyze_args["image_path"] = image_path
    if question:
        analyze_args["question"] = question
    else:
        analyze_args["question"] = (
            "请详细描述这张图片的内容，包括：文字内容、UI 元素、布局结构、"
            "可能的错误或异常信息。如果是截图，请描述截图中所有可见的界面元素。"
        )

    image_result = await _analyze_image(analyze_args)
    image_description = ""
    for item in image_result:
        if item.get("type") == "text":
            image_description += item["text"]

    if image_description.startswith("错误") or image_description.startswith("ERROR"):
        return [{"type": "text", "text": image_description}]

    # 3. 组合输出
    output_parts = [
        "=" * 50,
        "【图片内容描述】",
        "=" * 50,
        "",
        image_description.strip(),
        "",
    ]

    if user_text:
        output_parts.extend([
            "=" * 50,
            "【用户文字】",
            "=" * 50,
            "",
            user_text,
            "",
        ])

    if question:
        output_parts.extend([
            "=" * 50,
            "【针对图片的提问】",
            "=" * 50,
            "",
            question,
            "",
        ])

    output_parts.extend([
        "---",
        "请基于以上图片描述和用户文字，继续回答用户的问题。",
    ])

    return [{"type": "text", "text": "\n".join(output_parts)}]
