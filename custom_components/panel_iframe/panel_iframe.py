import os, yaml
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.const import CONF_ICON, CONF_URL
from .const import DOMAIN, VERSION
CONF_TITLE = "title"
CONF_REQUIRE_ADMIN = "require_admin"
CONFIG_FILE = 'panel_iframe.yml'

class PanelIframe:

    def __init__(self, hass):
        self.hass = hass
        hass.http.register_view(HassGateView)
        hass.components.frontend.async_register_built_in_panel(
            component_name="custom",
            sidebar_title="侧边栏管理",
            sidebar_icon="mdi:view-list-outline",
            frontend_url_path='/panel_iframe_custom',
            module_url="/panel_iframe",
            config={},
            require_admin=False,
        )

class HassGateView(HomeAssistantView):

    url = "/panel_iframe"
    requires_auth = False

    # 获取配置
    def config_get(self):
        if os.path.exists(CONFIG_FILE) == False:
            return []
        fs = open(CONFIG_FILE, encoding="UTF-8")
        data = yaml.load(fs, Loader=yaml.FullLoader)
        return data

    # 保存配置
    def config_save(self, data):
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(data, f)
        return self.config_get()

    async def get(self, request):
        return web.FileResponse('panel_iframe.js')

    async def post(self, request):
        self.hass = request.app["hass"]        
        query = request.query
        data = await request.json()
        _type = query.get('type', '')
        _id = data.get('id', '')
        _list = self.config_get()
        l = len(_list)
        if _type == 'add':
            _list.append(data)
            return self.config_save(_list)
        elif _type == 'del':
            for i in range(l):
                if _list[i]['id'] == _id
                    del _list[i]
                    break
            return self.config_save(_list)
        elif _type == 'set':
            for i in range(l):
                if _list[i]['id'] == _id
                    _list[i] = data
                    break
            return self.config_save(_list)
        elif _type == 'get':
            return _list