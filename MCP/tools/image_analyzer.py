"""
识图工具 — 调用通义千问 DashScope 视觉模型解析图片内容。

使用 OpenAI 兼容接口，API Key 从 config.properties 读取，
无需每次调用时输入。
"""

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from config import qwen_api_key, qwen_base_url, qwen_vision_model, qwen_timeout

# ==================== 工具定义 ====================

_DEFAULT_MODEL = qwen_vision_model()

TOOLS = [
    {
        "name": "analyze_image",
        "description": (
            "分析图片内容并返回文字描述（使用通义千问视觉模型）。"
            "支持对图片提问，如 '图中有什么错误？'、'截图中红框里的文字是什么？'。"
            "支持常见图片格式（png/jpg/gif/webp/bmp）。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件的绝对路径。与 image_base64 二选一。",
                },
                "image_base64": {
                    "type": "string",
                    "description": "图片的 base64 编码（不含 data:image 前缀）。与 image_path 二选一。",
                },
                "question": {
                    "type": "string",
                    "description": "（可选）针对图片的具体问题。不传则返回图片的通用描述。",
                },
                "model": {
                    "type": "string",
                    "description": f"（可选）视觉模型名称，默认 {_DEFAULT_MODEL}。可选 qwen-vl-max / qwen-vl-plus",
                },
            },
            "required": [],
        },
    },
]

# ==================== 处理函数 ====================


async def handle_tool(name: str, arguments: dict[str, Any]) -> list:
    """路由工具调用到具体处理函数"""
    if name == "analyze_image":
        return await _analyze_image(arguments)
    return None  # 不匹配，让注册中心继续尝试其他模块


async def _analyze_image(args: dict[str, Any]) -> list:
    """调用 Qwen DashScope 视觉模型分析图片（支持文件路径和 base64 两种输入）"""
    image_path = args.get("image_path", "").strip()
    image_base64 = args.get("image_base64", "").strip()
    question = args.get("question", "").strip()
    model = args.get("model", "").strip() or _DEFAULT_MODEL

    # 1. 确定图片来源：base64 优先，否则读文件
    if image_base64:
        # 去掉可能存在的 data:image/xxx;base64, 前缀
        if image_base64.startswith("data:"):
            # 提取 mime 和 base64 部分
            header, b64_data = image_base64.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0] if ":" in header else "image/png"
        else:
            b64_data = image_base64
            mime_type = "image/png"  # 默认
        data_url = f"data:{mime_type};base64,{b64_data}"

    elif image_path:
        # 校验图片路径
        path = Path(image_path)
        if not path.exists():
            return [_text(f"错误：图片文件不存在 — {image_path}")]
        if not path.is_file():
            return [_text(f"错误：路径不是文件 — {image_path}")]

        # 读取并编码图片
        try:
            image_bytes = path.read_bytes()
            image_b64 = base64.b64encode(image_bytes).decode("ascii")
            mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
            data_url = f"data:{mime_type};base64,{image_b64}"
        except Exception as e:
            return [_text(f"错误：无法读取图片文件 — {e}")]
    else:
        return [_text("错误：请提供 image_path 或 image_base64 参数。")]

    # 3. 构造 OpenAI 兼容请求
    prompt = question if question else "请详细描述这张图片的内容，包括文字、UI 元素、布局等信息。"
    payload = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }).encode("utf-8")

    api_key = qwen_api_key()
    if not api_key:
        return [_text("错误：未配置 qwen_api_key，请在 config/config.properties 中设置。")]

    base_url = qwen_base_url().rstrip("/")
    url = f"{base_url}/chat/completions"
    req = Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })

    # 4. 发送请求
    try:
        with urlopen(req, timeout=qwen_timeout()) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            choices = body.get("choices", [])
            if not choices:
                return [_text("模型返回了空内容，请检查 API Key 或模型是否可用。")]
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                return [_text("模型返回了空内容。")]
            return [_text(content)]
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return [_text(f"API 请求失败 ({e.code})：{error_body[:500]}")]
    except URLError as e:
        return [_text(f"错误：无法连接 DashScope API ({base_url}) — {e.reason}")]
    except json.JSONDecodeError:
        return [_text("错误：API 返回了无法解析的响应。")]
    except Exception as e:
        return [_text(f"识图失败：{e}")]


def _text(content: str) -> dict:
    return {"type": "text", "text": content}
