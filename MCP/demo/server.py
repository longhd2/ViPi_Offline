"""Small WebSocket MCP endpoint for ViPi, limited to configured client IPs."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import ipaddress
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

from aiohttp import WSMsgType, web

VERSION = "0.0.1"
NUMBERS = {name: i for i, name in enumerate(["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín", "mười"])}
NUMBERS["tư"] = 4
NUMBER = r"(?:-?\d{1,7}|không|một|hai|ba|bốn|tư|năm|sáu|bảy|tám|chín|mười)"


def tool(name, description, pattern, text=False, read_only=True):
    schema = {"type": "object", "properties": {}, "additionalProperties": False}
    if text:
        schema["properties"]["text"] = {"type": "string", "minLength": 1, "maxLength": 128}
        schema["required"] = ["text"]
    return {
        "name": name, "description": description, "inputSchema": schema,
        "annotations": {"readOnlyHint": read_only, "idempotentHint": True, "destructiveHint": False},
        "_meta": {"vipi": {
            "intent": "mcp." + name, "version": VERSION,
            "patterns": [{"regex": pattern}],
            "slots": {"text": "segment_text"} if text else {},
            "exclusive": True, "route_priority": 150,
        }},
    }


TOOLS = [
    tool("demo.time", "Xem giờ hiện tại bằng MCP mẫu.", r"^(?:xem giờ mẫu|đồng hồ mẫu|xem giờ mcp)$"),
    tool("demo.add", "Cộng hai số. Ví dụ: cộng mẫu 7 với 5.", r"^cộng mẫu .+$", text=True),
    tool("demo.light", "Bật, tắt hoặc xem đèn mô phỏng, không điều khiển đèn thật.",
         r"^(?:bật|tắt|xem|kiểm tra)(?: trạng thái)? đèn (?:mẫu|mô phỏng)(?: mcp)?$", text=True, read_only=False),
]


class RpcError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


def normalized(value):
    return re.sub(r"\s+", " ", value.casefold()).strip(" .,!?:;")


def result(text, data):
    return {"content": [{"type": "text", "text": text}], "structuredContent": data, "isError": False}


class Demo:
    def __init__(self, timezone="Asia/Ho_Chi_Minh"):
        self.timezone = ZoneInfo(timezone)
        self.light_on = False
        self.calls = 0

    def call(self, name, arguments):
        definition = next((item for item in TOOLS if item["name"] == name), None)
        if definition is None:
            raise RpcError(-32602, "Không có công cụ này.")
        if not isinstance(arguments, dict):
            raise RpcError(-32602, "Tham số phải là một đối tượng.")
        if name == "demo.time":
            if arguments:
                raise RpcError(-32602, "Công cụ xem giờ không nhận tham số.")
            now = datetime.now(self.timezone)
            self.calls += 1
            return result(f"Đồng hồ MCP: {now.hour} giờ {now.minute} phút.", {"time": now.isoformat()})
        if (set(arguments) != {"text"} or not isinstance(arguments.get("text"), str)
                or not 1 <= len(arguments["text"]) <= 128):
            raise RpcError(-32602, "Cần câu lệnh text từ 1 đến 128 ký tự.")
        text = normalized(arguments["text"])
        if name == "demo.add":
            match = re.fullmatch(r"cộng mẫu (" + NUMBER + r") (?:với|cộng) (" + NUMBER + r")", text)
            if not match:
                raise RpcError(-32602, "Hãy nói: cộng mẫu 7 với 5.")
            def number(value):
                return NUMBERS[value] if value in NUMBERS else int(value)
            a, b = map(number, match.groups())
            if max(abs(a), abs(b)) > 1000000:
                raise RpcError(-32602, "Mỗi số cần nằm trong khoảng âm một triệu đến một triệu.")
            self.calls += 1
            return result(f"{a} cộng {b} bằng {a + b}.", {"a": a, "b": b, "sum": a + b})
        match = re.fullmatch(r"(bật|tắt|xem|kiểm tra)(?: trạng thái)? đèn (?:mẫu|mô phỏng)(?: mcp)?", text)
        if not match:
            raise RpcError(-32602, "Hãy nói: bật đèn mẫu, tắt đèn mẫu hoặc xem đèn mẫu.")
        if match[1] in ("bật", "tắt"):
            self.light_on = match[1] == "bật"
        self.calls += 1
        return result("Đèn mô phỏng MCP đang " + ("bật." if self.light_on else "tắt."),
                      {"simulated": True, "on": self.light_on})


def create_app(config):
    networks = [ipaddress.ip_network(value, strict=False) for value in config["allowed_clients"]]
    if not networks:
        raise ValueError("Cần khai báo allowed_clients.")
    demo = Demo(config.get("timezone", "Asia/Ho_Chi_Minh"))
    connections = set()

    @web.middleware
    async def local_clients(request, handler):
        try:
            peer = ipaddress.ip_address(request.remote or "")
            permitted = any(peer in network for network in networks)
        except ValueError:
            permitted = False
        # This service has no browser interface and does not trust forwarded headers.
        if not permitted or request.headers.get("Origin") is not None:
            raise web.HTTPForbidden(text="Client not allowed")
        return await handler(request)

    app = web.Application(middlewares=[local_clients], client_max_size=16384)

    async def health(request):
        return web.json_response({"ok": True, "name": "ViPi MCP Demo", "version": VERSION,
                                  "tools": len(TOOLS), "calls": demo.calls})

    async def websocket(request):
        ws = web.WebSocketResponse(heartbeat=20, max_msg_size=16384)
        await ws.prepare(request)
        initialized, ready = False, False
        connections.add(ws)
        try:
            async for message in ws:
                if message.type != WSMsgType.TEXT:
                    if message.type == WSMsgType.ERROR:
                        break
                    continue
                identifier = None
                try:
                    try:
                        data = json.loads(message.data)
                    except (ValueError, TypeError):
                        raise RpcError(-32700, "Invalid JSON")
                    if not isinstance(data, dict) or data.get("jsonrpc") != "2.0" or not isinstance(data.get("method"), str):
                        raise RpcError(-32600, "Invalid request")
                    identifier = data.get("id")
                    if "id" in data and (type(identifier) not in (int, str) or len(str(identifier)) > 128):
                        identifier = None
                        raise RpcError(-32600, "Invalid id")
                    params = data.get("params", {})
                    if not isinstance(params, dict):
                        raise RpcError(-32602, "Invalid params")
                    method = data["method"]
                    if "id" not in data:
                        if method == "notifications/initialized" and initialized:
                            ready = True
                        continue
                    if method == "initialize":
                        initialized, ready = True, False
                        value = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {"listChanged": False}},
                                 "serverInfo": {"name": "ViPi MCP Demo", "version": VERSION}}
                    elif not ready:
                        raise RpcError(-32002, "Client chưa hoàn tất khởi tạo.")
                    elif method == "ping":
                        value = {}
                    elif method == "tools/list":
                        value = {"tools": TOOLS}
                    elif method == "tools/call":
                        value = demo.call(params.get("name"), params.get("arguments", {}))
                    else:
                        raise RpcError(-32601, "Method not found")
                    await ws.send_json({"jsonrpc": "2.0", "id": identifier, "result": value})
                except RpcError as error:
                    await ws.send_json({"jsonrpc": "2.0", "id": identifier,
                                        "error": {"code": error.code, "message": error.message}})
        finally:
            connections.discard(ws)
        return ws

    async def shutdown(app):
        await asyncio.gather(*(ws.close(code=1001, message=b"Service restarting") for ws in tuple(connections)))

    app.on_shutdown.append(shutdown)
    app.router.add_get("/health", health)
    app.router.add_get("/mcp", websocket)
    return app


def main():
    parser = argparse.ArgumentParser(description="MCP mẫu dành cho ViPi Server")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    host, port = config.get("listen", "127.0.0.1"), config.get("port", 8765)
    if not ipaddress.ip_address(host).is_private or type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("Dùng địa chỉ LAN/loopback và cổng từ 1024 đến 65535.")
    web.run_app(create_app(config), host=host, port=port, access_log=None)


if __name__ == "__main__":
    main()
