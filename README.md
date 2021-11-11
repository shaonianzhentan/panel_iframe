# panel_iframe
侧边栏面板管理

[![hacs_badge](https://img.shields.io/badge/Home-Assistant-%23049cdb)](https://www.home-assistant.io/)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

官方文档：https://www.home-assistant.io/integrations/panel_iframe/

## 安装方式

安装完成重启HA，刷新一下页面，在集成里搜索`侧边栏面板`即可

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=panel_iframe)

## 使用方式

介绍
```yaml
panel_iframe:
  full_router:
    title: 全屏显示
    url: http://192.168.1.1
  page_router:
    title: 打开新页面
    url: http://192.168.1.1
  ha_page1:
    title: 内置页面1
    url: /config/automation/dashboard
    icon: mdi:fridge
  otherapp:
    title: 默认显示
    url: /otherapp
    require_admin: true
```

示例
```yaml
panel_iframe:
  full_node_red:
    title: NodeRED
    icon: mdi:resistor-nodes
    url: /node-red/
  full_aria2:
    title: 下载管理
    icon: mdi:cloud-download
    url: /local/AriaNg/index.html
  full_homebridge:
    title: Homebridge
    icon: mdi:home-heart
    url: 8581
  full_kodbox:
    title: Homebridge
    icon: mdi:file-cloud
    url: 89
  full_docker:
    title: Docker
    icon: mdi:docker
    url: /docker-portainer/
  ha_config_integrations:
    title: 集成
    url: /config/integrations
    icon: mdi:puzzle
  ha_config_automation:
    title: 自动化
    url: /config/automation/dashboard
    icon: mdi:robot
  ha_config_server_control:
    title: 服务控制
    url: /config/server_control
    icon: mdi:robot
  page_github:
    title: GitHub
    icon: mdi:github
    url: https://github.com/shaonianzhentan/panel_iframe
  webssh:
    title: WebSSH
    icon: mdi:ssh
    url: /ssh/host/127.0.0.1
```