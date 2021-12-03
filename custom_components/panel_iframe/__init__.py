from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant import config as conf_util
from homeassistant.const import CONF_ICON, CONF_URL
import urllib, uuid, hashlib

from .const import DOMAIN

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

def md5(data):
    return hashlib.md5(data.encode(encoding='UTF-8')).hexdigest()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.http.register_static_path("/panel_iframe_www", hass.config.path("custom_components/" + DOMAIN + "/www"), False)
    # 添加面板
    cfg = entry.data
    mode = cfg.get('mode')
    title = cfg.get('title')
    icon = cfg.get('icon')
    url_path = md5(title)
    url = cfg.get('url')
    require_admin = cfg.get('require_admin')
    hass.components.frontend.async_register_built_in_panel("iframe", title, icon, url_path,
        {"url": f"/panel_iframe_www/index.html?v={uuid.uuid1().hex}&mode={mode}&url={urllib.parse.quote(url)}"},
        require_admin=require_admin,
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    cfg = entry.data
    title = cfg.get('title')
    url_path = md5(title)
    hass.components.frontend.async_remove_panel(url_path)
    return True