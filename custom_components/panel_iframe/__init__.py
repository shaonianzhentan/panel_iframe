from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant import config as conf_util
from homeassistant.const import CONF_ICON, CONF_URL
import urllib, uuid

from .const import DOMAIN

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.http.register_static_path("/panel_iframe_www", hass.config.path("custom_components/" + DOMAIN + "/www"), False)
    # 删除面板
    frontend_panels = hass.data.get("frontend_panels", {})
    for panel in frontend_panels:
        if panel.find("panel_iframe_") == 0:
            hass.components.frontend.async_remove_panel(panel)
    # 添加面板
    config = await conf_util.async_hass_config_yaml(hass)        
    panels = config.get(DOMAIN, {})
    for url_path, info in panels.items():
        mode = 0
        # 全屏显示
        if url_path.find('full_') == 0:
            mode = 1
        elif url_path.find('page_') == 0:
            mode = 2
        elif url_path.find('ha_') == 0:
            mode = 3

        url_path = 'panel_iframe_' + url_path
        hass.components.frontend.async_register_built_in_panel(
            "iframe",
            info.get("title"),
            info.get(CONF_ICON, "mdi:link-box-outline"),
            url_path,
            {"url": f"/panel_iframe_www/index.html?v={uuid.uuid1().hex}&mode={mode}&url={urllib.parse.quote(info[CONF_URL])}"},
            require_admin=info.get("require_admin", False),
        )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    
    return True