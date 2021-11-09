from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .panel_iframe import PanelIframe

unique_id = DOMAIN + '-shaonianzhentan'
CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[unique_id] = PanelIframe(hass)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[unique_id] = PanelIframe(hass)
    return True