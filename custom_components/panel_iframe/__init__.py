from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel
import homeassistant.helpers.config_validation as cv
import asyncio
from .manifest import manifest
from .http_proxy import HttpProxy

DOMAIN = manifest.domain
VERSION = manifest.version

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.http.async_register_static_paths(
        [ StaticPathConfig("/panel_iframe_www", hass.config.path("custom_components/" + DOMAIN + "/www"), False) ]
    )
    # 添加面板
    cfg = entry.options
    url_path = entry.entry_id
    title = entry.title
    mode = cfg.get('mode')
    icon = cfg.get('icon')
    url = cfg.get('url')
    require_admin = cfg.get('require_admin')
    proxy_access = cfg.get('proxy_access', False)

    if url is not None:
        module_url = f"/panel_iframe_www/panel_iframe.js?v={VERSION}"

        if proxy_access:
            proxy = HttpProxy(url)
            proxy.register(hass.http.app.router)
            url = proxy.get_url()

        await async_register_panel(hass,
            frontend_url_path=url_path,
            webcomponent_name="ha-panel_iframe",
            sidebar_title=title,
            sidebar_icon=icon,
            module_url=module_url,
            config={
                'mode': mode,
                'url': url
            },
            require_admin=require_admin
          )
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def update_listener(hass, entry):
    """Handle options update."""
    await async_unload_entry(hass, entry)
    await asyncio.sleep(1)
    await async_setup_entry(hass, entry)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    url_path = entry.entry_id
    hass.components.frontend.async_remove_panel(url_path)
    # 移除路由监听
    return True