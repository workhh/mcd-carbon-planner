"""麦当劳 MCP Streamable HTTP 客户端（零第三方依赖）.

通过环境变量 MCD_MCP_TOKEN 提供凭据，避免任何硬编码密钥。
未设置 Token 时自动进入演示模式（使用内置示例菜单数据），
便于评审与用户在无凭据环境下体验完整功能。
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field

MCP_ENDPOINT = "https://mcp.mcd.cn"
TOKEN_ENV = "MCD_MCP_TOKEN"
# 官方限流：600 次/分钟，客户端侧保守节流
MIN_REQUEST_INTERVAL = 0.15


@dataclass
class McpTool:
    """MCP 工具描述."""
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)


class McpError(RuntimeError):
    """MCP 调用失败."""


class McdMcpClient:
    """麦当劳 MCP 客户端.

    用法::

        client = McdMcpClient.from_env()
        tools = client.list_tools()
        result = client.call_tool("query-meals", {"storeId": "..."})
    """

    def __init__(self, token: str | None = None, endpoint: str = MCP_ENDPOINT,
                 demo: bool = False) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.demo = demo or not token
        self._session_id: str | None = None
        self._req_id = 0
        self._last_call = 0.0
        if self.demo:
            from .demo_data import DEMO_MENU, DEMO_TOOLS
            self._demo_tools = DEMO_TOOLS
            self._demo_menu = DEMO_MENU
        else:
            self._initialize()

    # ------------------------------------------------------------------ 构造
    @classmethod
    def from_env(cls) -> "McdMcpClient":
        return cls(token=os.environ.get(TOKEN_ENV))

    # ------------------------------------------------------------ JSON-RPC
    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _throttle(self) -> None:
        gap = time.monotonic() - self._last_call
        if gap < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - gap)
        self._last_call = time.monotonic()

    def _rpc(self, method: str, params: dict | None = None,
             notify: bool = False) -> dict:
        if self.demo:
            return self._demo_rpc(method, params or {})
        self._throttle()
        payload: dict = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }
        if not notify:
            # JSON-RPC 请求带 id；通知（notification）不带
            payload["id"] = self._next_id()
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {self.token}",
                **({"MCP-Session-Id": self._session_id}
                   if self._session_id else {}),
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                sid = resp.headers.get("MCP-Session-Id")
                if sid:
                    self._session_id = sid
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise McpError(f"MCP HTTP {exc.code}: {exc.read()[:300]!r}") from exc
        except urllib.error.URLError as exc:
            raise McpError(f"MCP 网络错误: {exc.reason}") from exc
        # 通知的响应可能是 202 空 body
        if not body.strip():
            return {}
        return self._parse_rpc_response(body)

    @staticmethod
    def _parse_rpc_response(body: str) -> dict:
        # 空 body（如 202 Accepted 的通知响应）
        if not body.strip():
            return {}
        # Streamable HTTP 可能返回 SSE（text/event-stream）或纯 JSON
        if body.lstrip().startswith("{"):
            data = json.loads(body)
        else:
            data = None
            for line in body.splitlines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    break
            if data is None:
                raise McpError("无法解析 MCP 响应（既非 JSON 也非 SSE data）")
        if "error" in data:
            raise McpError(f"MCP RPC 错误: {data['error']}")
        return data.get("result", {})

    def _initialize(self) -> None:
        self._rpc("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "mcd-carbon-planner", "version": "1.0.1"},
        })
        self._rpc("notifications/initialized", {}, notify=True)

    # -------------------------------------------------------------- 工具层
    def list_tools(self) -> list[McpTool]:
        """列出 MCP Server 提供的全部工具."""
        if self.demo:
            return list(self._demo_tools)
        result = self._rpc("tools/list", {})
        return [
            McpTool(name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}))
            for t in result.get("tools", [])
        ]

    def call_tool(self, name: str, arguments: dict) -> dict:
        """调用指定工具，返回结构化结果."""
        if self.demo:
            if name in ("query-meals", "query-meal-detail", "list-nutrition-foods"):
                return {"menu": self._demo_menu, "demo": True}
            return {"demo": True, "message": f"演示模式：{name} 未提供示例数据"}
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        # MCP 2025-03-26+ 支持结构化结果
        if isinstance(result.get("structuredContent"), dict):
            return result["structuredContent"]
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                try:
                    return json.loads(item["text"])
                except (json.JSONDecodeError, KeyError):
                    return {"text": item["text"]}
        return result

    # -------------------------------------------------- 演示模式（无 Token）
    def _demo_rpc(self, method: str, params: dict) -> dict:
        if method == "tools/list":
            return {"tools": [
                {"name": t.name, "description": t.description,
                 "inputSchema": t.input_schema}
                for t in self._demo_tools
            ]}
        if method in ("initialize", "notifications/initialized"):
            return {}
        if method == "tools/call":
            return self.call_tool(params.get("name", ""),
                                  params.get("arguments", {}))
        return {}
