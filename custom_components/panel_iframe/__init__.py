from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import urllib

from .const import DOMAIN, VERSION

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.http.register_static_path("/panel_iframe_www", hass.config.path("custom_components/" + DOMAIN + "/www"), False)
    # 添加面板
    cfg = entry.data
    url_path = entry.entry_id
    mode = cfg.get('mode')
    title = cfg.get('title')
    icon = cfg.get('icon')
    url = cfg.get('url')
    require_admin = cfg.get('require_admin')
    hass.components.frontend.async_register_built_in_panel("iframe", title, icon, url_path,
        {"url": f"/panel_iframe_www/index.html?v={VERSION}&mode={mode}&url={urllib.parse.quote(url)}"},
        require_admin=require_admin,
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    url_path = entry.entry_id
    hass.components.frontend.async_remove_panel(url_path)
    return True