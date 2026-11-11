"""把另一个 Web 服务反向代理到 Home Assistant 的同一域名下。"""
from __future__ import annotations

import asyncio
import logging
import ssl
from urllib.parse import urlsplit, urlunsplit

import aiohttp
from aiohttp import web

_LOGGER = logging.getLogger(__name__)

# 代理默认不校验上游 TLS 证书：多为内网自签名服务，且仅供个人使用。
_SSL_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

_HOP_BY_HOP_HEADERS = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }
)

# 请求头：Host/长度由 aiohttp 重新生成，HA 的令牌不转发给上游。
_SKIP_REQUEST_HEADERS = _HOP_BY_HOP_HEADERS | {
    "host",
    "content-length",
    "authorization",
    "accept-encoding",
    "sec-websocket-key",
    "sec-websocket-version",
    "sec-websocket-extensions",
    "sec-websocket-protocol",
    "sec-websocket-accept",
}

# 响应头：aiohttp 已自动解压响应体，长度/编码必须重新计算；
# 同时去掉上游的嵌入限制，否则 iframe 无法加载。
_SKIP_RESPONSE_HEADERS = _HOP_BY_HOP_HEADERS | {
    "content-length",
    "content-encoding",
    "date",
    "server",
    "x-frame-options",
    "content-security-policy",
    "content-security-policy-report-only",
    "strict-transport-security",
}

_TIMEOUT = aiohttp.ClientTimeout(total=60, connect=10)


def _normalize_url(url: str) -> str:
    """兼容只填端口的旧写法。"""
    url = url.strip()
    if url.isdigit():
        return f"http://localhost:{url}"
    if url.startswith(":"):
        return f"http://localhost{url}"
    return url


class HttpProxy:
    """代理单个上游服务；同一路径的路由只注册一次，可被多个配置项复用。"""

    def __init__(self, url: str, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._users: set[str] = set()
        self._active = False

        parsed = urlsplit(_normalize_url(url))
        route_path = parsed.path.strip("/")
        self.is_root = route_path == ""
        if self.is_root:
            route_path = parsed.netloc.replace(":", "").replace(".", "")
        self.proxy_path = route_path
        self.update(url)

    def register(self, router) -> None:
        """把通配路由注册到 HA 的 aiohttp 应用。"""
        router.add_route("*", f"/{self.proxy_path}/{{tail:.*}}", self.handler)

    def get_url(self, hostname: str = "") -> str:
        """返回面板可访问的代理地址。"""
        return f"{hostname}/{self.proxy_path}/"

    def update(self, url: str) -> None:
        """让已注册的路由指向新的上游地址。"""
        parsed = urlsplit(_normalize_url(url))
        self.scheme = parsed.scheme or "http"
        self.proxy_host = parsed.netloc

    def activate(self, entry_id: str) -> None:
        self._users.add(entry_id)
        self._active = True

    def deactivate(self, entry_id: str) -> None:
        self._users.discard(entry_id)
        if not self._users:
            self._active = False

    def _upstream_url(self, request: web.Request, scheme: str) -> str:
        path = request.rel_url.path
        if self.is_root:
            prefix = f"/{self.proxy_path}"
            if path.startswith(prefix):
                path = path[len(prefix) :] or "/"
            if not path.startswith("/"):
                path = f"/{path}"
        return urlunsplit((scheme, self.proxy_host, path, request.query_string, ""))

    @staticmethod
    def _request_headers(request: web.Request) -> dict[str, str]:
        return {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in _SKIP_REQUEST_HEADERS
        }

    def _rewrite_location(self, location: str) -> str:
        """把上游重定向地址改写成 HA 上的代理路径。"""
        parsed = urlsplit(location)
        if parsed.netloc and parsed.netloc != self.proxy_host:
            return location
        prefix = f"/{self.proxy_path}"
        path = parsed.path or "/"
        if not path.startswith(prefix):
            path = f"{prefix}/{path.lstrip('/')}"
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{path}{query}"

    async def handler(self, request: web.Request) -> web.StreamResponse:
        if not self._active:
            raise web.HTTPNotFound()
        if request.headers.get("Upgrade", "").lower() == "websocket":
            return await self.websocket_handler(request)
        return await self.http_handler(request)

    async def http_handler(self, request: web.Request) -> web.Response:
        target = self._upstream_url(request, self.scheme)
        try:
            async with self._session.request(
                request.method,
                target,
                headers=self._request_headers(request),
                data=await request.read(),
                allow_redirects=False,
                timeout=_TIMEOUT,
                ssl=_SSL_CONTEXT,
            ) as resp:
                body = await resp.read()
                status = resp.status
                headers = list(resp.headers.items())
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            _LOGGER.warning("代理请求失败 %s: %s", target, err)
            return web.Response(status=502, text="panel_iframe: upstream unavailable")

        response = web.Response(body=body, status=status)
        for key, value in headers:
            key_lower = key.lower()
            if key_lower in _SKIP_RESPONSE_HEADERS:
                continue
            if key_lower == "location":
                value = self._rewrite_location(value)
            if key_lower == "content-type":
                response.headers[key] = value
            else:
                response.headers.add(key, value)
        return response

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        protocols = [
            protocol.strip()
            for protocol in request.headers.get("Sec-WebSocket-Protocol", "").split(
                ","
            )
            if protocol.strip()
        ]
        ws_server = web.WebSocketResponse(protocols=protocols)
        await ws_server.prepare(request)

        scheme = "wss" if self.scheme == "https" else "ws"
        target = self._upstream_url(request, scheme)
        try:
            async with self._session.ws_connect(
                target,
                headers=self._request_headers(request),
                protocols=protocols,
                ssl=_SSL_CONTEXT,
            ) as ws_client:
                await self._pump(ws_server, ws_client)
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            _LOGGER.warning("代理 WebSocket 失败 %s: %s", target, err)
        return ws_server

    @staticmethod
    async def _pump(
        ws_server: web.WebSocketResponse, ws_client: aiohttp.ClientWebSocketResponse
    ) -> None:
        async def forward(ws_from, ws_to) -> None:
            async for msg in ws_from:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await ws_to.send_str(msg.data)
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    await ws_to.send_bytes(msg.data)
                elif msg.type in (
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                    aiohttp.WSMsgType.CLOSED,
                ):
                    await ws_to.close()
                    return

        tasks = [
            asyncio.create_task(forward(ws_server, ws_client)),
            asyncio.create_task(forward(ws_client, ws_server)),
        ]
        try:
            _, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            await ws_server.close()
