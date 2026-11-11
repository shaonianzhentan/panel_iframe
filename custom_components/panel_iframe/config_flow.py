from __future__ import annotations

import asyncio
import ssl
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

# Home Assistant 2026.9 起使用 Probatio 替代 voluptuous，
# 旧版本仍只有 voluptuous，这里做双向兼容。
try:
    import probatio as vol
except ImportError:  # pragma: no cover - 仅在旧版 HA 上生效
    import voluptuous as vol  # type: ignore[no-redef]

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import selector

from .manifest import manifest

MODE_LIST = {
    "0": "默认",
    "1": "全屏",
    "2": "新页面",
    "3": "内置页面",
}


def _normalize_proxy_url(url: str) -> str | None:
    """把代理目标地址规范化为绝对 http(s) 地址。

    缺省协议时自动补 http://（方便填写内网 host:port）；
    仅允许 http/https，且必须含有主机名，否则返回 None 表示无效。
    """
    url = url.strip()
    if not url:
        return None
    if "://" not in url:
        url = "http://" + url
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None
    # 去掉片段，保留协议/主机/路径/查询，路径缺省为根
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, "")
    )


# 提交时探测上游的超时；不校验 TLS（与代理默认行为一致）
_PROBE_TIMEOUT = aiohttp.ClientTimeout(total=5, connect=3)
_PROBE_SSL = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
_PROBE_SSL.check_hostname = False
_PROBE_SSL.verify_mode = ssl.CERT_NONE


class SimpleConfigFlow(ConfigFlow, domain=manifest.domain):
    """创建侧边栏面板。"""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required("title"): str}),
            )

        return self.async_create_entry(title=user_input["title"], data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """返回选项流，不再向 OptionsFlow.__init__ 传递配置项。"""
        flow = OptionsFlowHandler()
        # HA 2024.11 之前没有 self.config_entry，这里留一个兼容入口。
        flow._legacy_entry = config_entry
        return flow


class OptionsFlowHandler(OptionsFlow):
    """配置侧边栏面板。"""

    _legacy_entry: ConfigEntry | None = None

    @property
    def current_entry(self) -> ConfigEntry:
        """跨版本获取当前配置项。"""
        entry = getattr(self, "config_entry", None) or self._legacy_entry
        assert entry is not None
        return entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self.async_step_user(user_input)

    async def _check_proxy_reachable(self, url: str) -> bool:
        """提交时探测上游是否可达：任何 HTTP 响应都算可达，仅连接/超时视为不可达。"""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                url,
                timeout=_PROBE_TIMEOUT,
                ssl=_PROBE_SSL,
                allow_redirects=False,
            ):
                return True
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
            return False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        options = self.current_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    "icon", default=options.get("icon", "mdi:link-box-outline")
                ): selector({"icon": {}}),
                vol.Required("url", default=options.get("url", "")): str,
                vol.Required("mode", default=options.get("mode", "0")): vol.In(
                    MODE_LIST
                ),
                vol.Required(
                    "require_admin", default=options.get("require_admin", False)
                ): bool,
                vol.Required(
                    "proxy_access", default=options.get("proxy_access", False)
                ): bool,
            }
        )

        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=schema, errors=errors
            )

        user_input["icon"] = user_input["icon"].strip().replace("mdi-", "mdi:")
        raw_url = user_input["url"].strip()
        user_input["url"] = raw_url

        # 内置页面禁止使用代理
        if user_input["mode"] == "3":
            user_input["proxy_access"] = False

        # 代理模式：智能规范化并校验目标地址
        if user_input["proxy_access"]:
            normalized = _normalize_proxy_url(raw_url)
            if normalized is None:
                errors["url"] = "proxy_url_invalid"
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors=errors
                )
            user_input["url"] = normalized
            if not await self._check_proxy_reachable(normalized):
                errors["url"] = "proxy_url_unreachable"
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors=errors
                )

        return self.async_create_entry(title="", data=user_input)
