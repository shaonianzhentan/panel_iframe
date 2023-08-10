from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import urllib

from .manifest import manifest
DOMAIN = manifest.domain
VERSION = manifest.version

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.http.register_static_path("/panel_iframe_www", hass.config.path("custom_components/" + DOMAIN + "/www"), False)
    # 添加面板
    cfg = entry.options
    url_path = entry.entry_id
    title = entry.title
    mode = cfg.get('mode')
    icon = cfg.get('icon')
    url = cfg.get('url')
    require_admin = cfg.get('require_admin')
    if url is not None:
        hass.components.frontend.async_register_built_in_panel("iframe", title, icon, url_path,
            {"url": f"/panel_iframe_www/index.html?v={VERSION}&mode={mode}&url={urllib.parse.quote(url)}"},
            require_admin=require_admin,
        )
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def update_listener(hass, entry):
    """Handle options update."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    url_path = entry.entry_id
    hass.components.frontend.async_remove_panel(url_path)
    return True