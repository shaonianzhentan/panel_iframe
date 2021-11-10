# panel_iframe
侧边栏面板管理增强版

官方文档：https://www.home-assistant.io/integrations/panel_iframe/


```yaml
panel_iframe:
  full_router:
    title: "全屏显示"
    url: "http://192.168.1.1"
  page_router:
    title: "打开新页面"
    url: "http://192.168.1.1"
  ha_page1:
    title: "内置页面1"
    url: "http://192.168.1.5"
    icon: mdi:fridge
  otherapp:
    title: "Other App"
    url: "/otherapp"
    require_admin: true
```