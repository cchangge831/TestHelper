"""
浏览器控制工具 - 基于 Playwright 实现浏览器自动化和内容识别。

支持两套工作模式：
1. 自动化模式：启动新浏览器，执行导航/点击/输入/截图等操作
2. 连接模式：连接到用户已有的 Chrome 实例，分析页面内容和错误
"""

import base64
from typing import Any

from config import browser_type, browser_headless, browser_timeout, chrome_debug_port

# ==================== 模块级状态 ====================

_playwright = None
_browser = None
_page = None
_context = None


async def _get_playwright():
    """延迟导入 + 懒启动 Playwright"""
    global _playwright
    if _playwright is None:
        from playwright.async_api import async_playwright
        _playwright = await async_playwright().start()
    return _playwright


async def _ensure_browser(headless: bool | None = None):
    """确保有可用的浏览器实例"""
    global _browser, _context, _page

    if _browser and _browser.is_connected():
        if not _page or _page.is_closed():
            _context = await _browser.new_context()
            _page = await _context.new_page()
        return _page

    pw = await _get_playwright()
    headless = headless if headless is not None else browser_headless()
    bt = browser_type()
    timeout = browser_timeout()

    _browser = await pw.chromium.launch(
        headless=headless,
        channel=bt if bt != "chromium" else None,
    )
    _context = await _browser.new_context()
    _page = await _context.new_page()
    _page.set_default_timeout(timeout)
    return _page


async def _connect_existing(port: int = 0) -> str:
    """连接到已有 Chrome 实例"""
    global _browser, _context, _page

    if port <= 0:
        port = chrome_debug_port()

    try:
        pw = await _get_playwright()
        _browser = await pw.chromium.connect_over_cdp(f"http://localhost:{port}")
        contexts = _browser.contexts
        if contexts:
            _context = contexts[0]
            pages = _context.pages
            _page = pages[0] if pages else await _context.new_page()
        else:
            _context = await _browser.new_context()
            _page = await _context.new_page()
        return f"成功连接到 Chrome (端口 {port})，当前页面：{_page.url}"
    except Exception as e:
        return f"连接 Chrome 失败：{e}。请确保 Chrome 已用 --remote-debugging-port={port} 参数启动。"


async def _cleanup():
    """清理浏览器资源"""
    global _browser, _context, _page
    try:
        if _page:
            await _page.close()
        if _context:
            await _context.close()
        if _browser:
            await _browser.close()
    except Exception:
        pass
    _page = None
    _context = None
    _browser = None


# ==================== 工具定义 ====================

TOOLS = [
    {
        "name": "browser_connect",
        "description": "连接到用户已有的 Chrome 浏览器实例，用于分析当前页面内容。用户需先以 chrome.exe --remote-debugging-port=9222 启动 Chrome。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "port": {
                    "type": "integer",
                    "description": "Chrome 远程调试端口，默认 9222",
                },
            },
        },
    },
    {
        "name": "browser_navigate",
        "description": "导航到指定 URL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "目标 URL（需包含 http:// 或 https://）",
                },
                "headless": {
                    "type": "boolean",
                    "description": "是否无头模式（默认 false，显示浏览器窗口）",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "browser_screenshot",
        "description": "对当前页面截图。可选截取全页面或指定元素。截图以 base64 返回，AI 可直接查看。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "full_page": {
                    "type": "boolean",
                    "description": "是否截取全页面（默认 false，仅可见区域）",
                },
                "selector": {
                    "type": "string",
                    "description": "CSS 选择器，仅截取指定元素",
                },
            },
        },
    },
    {
        "name": "browser_click",
        "description": "点击页面元素（支持 CSS 选择器或文本匹配）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS 选择器，如 #login-btn",
                },
                "text": {
                    "type": "string",
                    "description": "按可见文本匹配，如 '登录'",
                },
            },
        },
    },
    {
        "name": "browser_type",
        "description": "在输入框中输入文本",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "输入框的 CSS 选择器",
                },
                "text": {
                    "type": "string",
                    "description": "要输入的文本",
                },
                "clear": {
                    "type": "boolean",
                    "description": "输入前是否清空已有内容（默认 true）",
                },
            },
            "required": ["selector", "text"],
        },
    },
    {
        "name": "browser_get_content",
        "description": "获取当前页面内容：标题、URL、可见文本。用于分析 Bug 或了解页面状态。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_screenshot": {
                    "type": "boolean",
                    "description": "是否同时截图（默认 false）",
                },
                "selector": {
                    "type": "string",
                    "description": "仅提取指定元素的文本",
                },
            },
        },
    },
    {
        "name": "browser_get_console",
        "description": "获取浏览器控制台日志（error/warning/info），用于调试前端问题",
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "description": "日志级别：error / warning / info / all（默认 error）",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回条数上限（默认 30）",
                },
            },
        },
    },
    {
        "name": "browser_evaluate",
        "description": "在页面中执行 JavaScript 代码并返回结果",
        "inputSchema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "要执行的 JavaScript 代码",
                },
            },
            "required": ["script"],
        },
    },
    {
        "name": "browser_close",
        "description": "关闭浏览器实例，释放资源",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

# ==================== 处理函数 ====================


async def handle_tool(name: str, arguments: dict[str, Any]) -> list:
    """路由工具调用"""
    handlers = {
        "browser_connect": _handle_connect,
        "browser_navigate": _handle_navigate,
        "browser_screenshot": _handle_screenshot,
        "browser_click": _handle_click,
        "browser_type": _handle_type,
        "browser_get_content": _handle_get_content,
        "browser_get_console": _handle_get_console,
        "browser_evaluate": _handle_evaluate,
        "browser_close": _handle_close,
    }
    handler = handlers.get(name)
    if handler:
        return await handler(arguments)
    return [_text(f"未知工具: {name}", is_error=True)]


async def _handle_connect(args: dict) -> list:
    port = args.get("port", 0)
    result = await _connect_existing(port)
    return [_text(result)]


async def _handle_navigate(args: dict) -> list:
    url = args["url"]
    headless = args.get("headless")
    try:
        page = await _ensure_browser(headless=headless)
        await page.goto(url, wait_until="domcontentloaded")
        title = await page.title()
        return [_text(f"已导航到：{url}\n页面标题：{title}")]
    except Exception as e:
        return [_text(f"导航失败：{e}", is_error=True)]


async def _handle_screenshot(args: dict) -> list:
    full_page = args.get("full_page", False)
    selector = args.get("selector")

    try:
        if _page is None or _page.is_closed():
            return [_text("没有打开的页面，请先执行 browser_navigate 或 browser_connect。", is_error=True)]

        if selector:
            element = await _page.query_selector(selector)
            if not element:
                return [_text(f"未找到元素：{selector}", is_error=True)]
            screenshot = await element.screenshot()
        else:
            screenshot = await _page.screenshot(full_page=full_page)

        b64 = base64.b64encode(screenshot).decode("ascii")
        return [
            {"type": "image", "data": b64, "mimeType": "image/png"},
            {"type": "text", "text": f"截图完成（{len(screenshot)} bytes）"},
        ]
    except Exception as e:
        return [_text(f"截图失败：{e}", is_error=True)]


async def _handle_click(args: dict) -> list:
    selector = args.get("selector", "")
    text = args.get("text", "")

    try:
        if _page is None or _page.is_closed():
            return [_text("没有打开的页面。", is_error=True)]

        if text:
            element = _page.get_by_text(text).first
        elif selector:
            element = _page.locator(selector).first
        else:
            return [_text("请提供 selector 或 text 参数。", is_error=True)]

        await element.click()
        return [_text("已点击元素")]
    except Exception as e:
        return [_text(f"点击失败：{e}", is_error=True)]


async def _handle_type(args: dict) -> list:
    selector = args["selector"]
    text = args["text"]
    clear = args.get("clear", True)

    try:
        if _page is None or _page.is_closed():
            return [_text("没有打开的页面。", is_error=True)]

        element = _page.locator(selector).first
        if clear:
            await element.clear()
        await element.type(text)
        return [_text(f"已在 [{selector}] 中输入：{text}")]
    except Exception as e:
        return [_text(f"输入失败：{e}", is_error=True)]


async def _handle_get_content(args: dict) -> list:
    include_screenshot = args.get("include_screenshot", False)
    selector = args.get("selector")

    try:
        if _page is None or _page.is_closed():
            return [_text("没有打开的页面。", is_error=True)]

        url = _page.url
        title = await _page.title()

        if selector:
            element = _page.locator(selector).first
            text_content = await element.inner_text()
        else:
            text_content = await _page.inner_text("body")

        if len(text_content) > 8000:
            text_content = text_content[:8000] + "\n\n... (内容过长已截断)"

        result = f"URL: {url}\n标题: {title}\n\n--- 页面内容 ---\n{text_content}"
        response = [_text(result)]

        if include_screenshot:
            screenshot = await _page.screenshot(full_page=False)
            b64 = base64.b64encode(screenshot).decode("ascii")
            response.insert(0, {"type": "image", "data": b64, "mimeType": "image/png"})

        return response
    except Exception as e:
        return [_text(f"获取内容失败：{e}", is_error=True)]


async def _handle_get_console(args: dict) -> list:
    level = args.get("level", "error")
    limit = args.get("limit", 30)

    try:
        if _page is None or _page.is_closed():
            return [_text("没有打开的页面。", is_error=True)]

        return [_text("控制台日志需要在页面加载前设置监听。当前页面无缓存日志。"
                       "请使用 browser_evaluate 执行代码或重新加载页面。")]
    except Exception as e:
        return [_text(f"获取控制台日志失败：{e}", is_error=True)]


async def _handle_evaluate(args: dict) -> list:
    script = args["script"]

    try:
        if _page is None or _page.is_closed():
            return [_text("没有打开的页面。", is_error=True)]

        result = await _page.evaluate(script)
        return [_text(f"执行结果：{result}")]
    except Exception as e:
        return [_text(f"执行脚本失败：{e}", is_error=True)]


async def _handle_close(args: dict) -> list:
    await _cleanup()
    return [_text("浏览器已关闭")]


def _text(content: str, is_error: bool = False) -> dict:
    prefix = "ERROR: " if is_error else ""
    return {"type": "text", "text": prefix + content}
