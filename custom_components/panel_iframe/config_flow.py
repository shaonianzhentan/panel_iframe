from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class SimpleConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        if user_input is None:
            errors = {}
            mode_list = {
                '0': '默认',
                '1': '全屏',
                '2': '新页面',
                '3': '内置页面'
            }
            DATA_SCHEMA = vol.Schema({
                vol.Required("title"): str,
                vol.Required("icon", default='mdi:link-box-outline'): str,
                vol.Required("url"): str,
                vol.Required("mode", default=['0']): vol.In(mode_list),
                vol.Required("require_admin", default=False): bool,
            })
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

        return self.async_create_entry(title=user_input['title'], data=user_input)