"""侧边栏面板集成。"""
from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .http_proxy import HttpProxy
from .manifest import manifest

DOMAIN = manifest.domain
VERSION = manifest.version

WWW_PATH = Path(__file__).parent / "www"
WWW_URL = "/panel_iframe_www"
DATA_WWW_REGISTERED = f"{DOMAIN}_www_registered"
DATA_PROXIES = f"{DOMAIN}_proxies"
DATA_ENTRY_PROXIES = f"{DOMAIN}_entry_proxies"

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """组件级只注册一次静态资源，避免多配置项/重载时重复挂载路由。"""
    await _async_register_www(hass)
    return True


async def _async_register_www(hass: HomeAssistant) -> None:
    """静态资源只注册一次，避免重载/多配置项时重复挂载路由。"""
    if hass.data.get(DATA_WWW_REGISTERED):
        return
    await hass.http.async_register_static_paths(
        [StaticPathConfig(WWW_URL, str(WWW_PATH), False)]
    )
    hass.data[DATA_WWW_REGISTERED] = True


def _async_activate_proxy(hass: HomeAssistant, entry: ConfigEntry, url: str) -> str:
    """复用同一路径的代理路由，返回面板可访问的地址。"""
    proxies: dict[str, HttpProxy] = hass.data.setdefault(DATA_PROXIES, {})
    entry_proxies: dict[str, HttpProxy] = hass.data.setdefault(
        DATA_ENTRY_PROXIES, {}
    )

    candidate = HttpProxy(url, async_get_clientsession(hass))
    previous = entry_proxies.get(entry.entry_id)
    if previous is not None and previous.proxy_path != candidate.proxy_path:
        previous.deactivate(entry.entry_id)
        entry_proxies.pop(entry.entry_id, None)

    proxy = proxies.get(candidate.proxy_path)
    if proxy is None:
        candidate.register(hass.http.app.router)
        proxies[candidate.proxy_path] = candidate
        proxy = candidate
    else:
        proxy.update(url)

    proxy.activate(entry.entry_id)
    entry_proxies[entry.entry_id] = proxy
    return proxy.get_url()


def _async_deactivate_proxy(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """配置项卸载后停止代理，避免残留路由继续转发。"""
    proxy: HttpProxy | None = hass.data.get(DATA_ENTRY_PROXIES, {}).pop(
        entry.entry_id, None
    )
    if proxy is not None:
        proxy.deactivate(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """从配置项加载侧边栏面板。

    HA 2024.x 要求返回 bool；新版 HA 允许返回 None，
    但对自定义集成仍明确兼容 bool 返回值，故统一返回 True。
    """
    entry.async_on_unload(entry.add_update_listener(update_listener))
    await _async_register_www(hass)

    cfg = entry.options
    url = cfg.get("url")
    if not url:
        return True

    if cfg.get("proxy_access", False):
        url = _async_activate_proxy(hass, entry, url)

    await async_register_panel(
        hass,
        frontend_url_path=entry.entry_id,
        webcomponent_name="ha-panel_iframe",
        sidebar_title=entry.title,
        sidebar_icon=cfg.get("icon"),
        module_url=f"{WWW_URL}/panel_iframe.js?v={VERSION}",
        config={"mode": cfg.get("mode", "0"), "url": url},
        require_admin=bool(cfg.get("require_admin", False)),
    )
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """选项更新后由 HA 统一重载配置项。

    必须是协程：HA 会用 hass.async_create_task 调用更新监听器。
    """
    hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    url_path = entry.entry_id
    # warn_if_unknown 在 2024.7 与 2026.11 均受支持，避免移除未注册面板时告警
    frontend.async_remove_panel(hass, url_path, warn_if_unknown=False)
    _async_deactivate_proxy(hass, entry)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _async_deactivate_proxy(hass, entry)
