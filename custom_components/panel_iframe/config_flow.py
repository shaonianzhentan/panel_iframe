from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.data_entry_flow import FlowResult

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry

from .manifest import manifest

mode_list = {
    '0': '默认',
    '1': '全屏',
    '2': '新页面',
    '3': '内置页面'
}

class SimpleConfigFlow(ConfigFlow, domain=manifest.domain):

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        if user_input is None:
            errors = {}
            DATA_SCHEMA = vol.Schema({
                vol.Required("title"): str,
            })
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

        return self.async_create_entry(title=user_input['title'], data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry):
        return OptionsFlowHandler(entry)


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is None:
            options = self.config_entry.options
            errors = {}
            DATA_SCHEMA = vol.Schema({
                vol.Required("icon", default=options.get('icon', 'mdi:link-box-outline')): str,
                vol.Required("url", default=options.get('url', '')): str,
                vol.Required("require_admin", default=options.get('require_admin', False)): bool,
                vol.Required("mode", default=options.get('mode', '0')): vol.In(mode_list),
            })
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
        # 选项更新
        user_input['icon'] = user_input['icon'].strip().replace('mdi-', 'mdi:')
        user_input['url'] = user_input['url'].strip()
        return self.async_create_entry(title='', data=user_input)