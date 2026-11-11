# 侧边栏面板

[![hacs_badge](https://img.shields.io/badge/Home-Assistant-%23049cdb)](https://www.home-assistant.io/)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)


![visit](https://visitor-badge.laobi.icu/badge?page_id=shaonianzhentan.panel_iframe&left_text=visit)

## 安装方式

安装完成重启HA，刷新一下页面，在集成里搜索`侧边栏面板`即可。

Home Assistant 2026.11 起 HACS 已内置为「Marketplace」，可直接在 `设置 → Marketplace` 中搜索安装，无需再单独安装 HACS。

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=panel_iframe)

注意：长按侧边栏面板标题`Home Assistant`可隐藏菜单

## 兼容性

- 已适配 Home Assistant 2026.11：面板使用标准自定义元素实现，不再依赖前端内部的 LitElement；配置流兼容新版 Probatio 校验。
- 修改选项后通过 HA 官方的配置项重载机制生效，无需重启。
- 升级后如仍显示旧面板，请强制刷新浏览器一次（前端脚本地址带版本号，正常会自动更新）。

## 使用示例

添加集成时先填写「名称」，保存后会进入配置页，在其中设置链接、显示模式、代理访问、图标与管理员可见等。下面给出常见场景。

### 显示模式说明

| 模式 | 效果 | 适用场景 |
| --- | --- | --- |
| 默认（嵌入式） | 在侧边栏面板区域内直接嵌入网页 | 大多数内网页面、监控墙 |
| 全屏 | 占满整个内容区，隐藏侧边栏干扰 | Grafana、监控大屏、轮播 |
| 新页面 | 点击后在浏览器新标签页打开 | 禁止被 iframe 嵌入 / HTTPS 外部站点 |
| 内置页面 | 在 HA 内部跳转到指定 HA 页面 | 直达仪表盘、配置页、历史页等 |

### 示例一：嵌入 Node-RED 编辑器（代理访问）

- 场景：Node-RED 运行在内网 `http://192.168.1.10:1880`，不想把 1880 端口暴露到公网。
- 配置：
  - 名称：`Node-RED`
  - 链接：`192.168.1.10:1880`（可省略 `http://`，自动按 http 处理）
  - 显示模式：默认
  - 代理访问：开启
- 原理：插件把 Node-RED 反向代理到 HA 同一域名下（如 `https://my.ha.com/nodered/`），公网只需暴露 HA 本身。保存时会自动探测该地址是否可达。
- 注意：若 HA 跑在容器里，填的 `localhost` 指向的是容器自身而非宿主机；应使用宿主机真实内网 IP 或 `host.docker.internal`。

### 示例二：嵌入 Grafana 监控大屏（全屏）

- 名称：`监控大屏`
- 链接：`https://grafana.example.com`（或经代理的内网地址）
- 显示模式：全屏
- 说明：全屏模式隐藏侧边栏与顶栏，适合长期轮播监控。

### 示例三：打开外部 HTTPS 站点（新页面）

- 场景：部分站点带 `X-Frame-Options` / `CSP` 禁止被 iframe 嵌入，或 HA 是 http 而目标是 https（混合内容被浏览器拦截）。
- 名称：`天气`
- 链接：`https://www.windy.com`
- 显示模式：新页面
- 效果：点击侧边栏后在新的浏览器标签页打开，规避跨域 / 混合内容限制。

### 示例四：侧边栏直达 HA 内部页面（内置页面）

- 名称：`配置`
- 显示模式：内置页面
- 链接：`/config`（也可填 `/lovelace/my_dashboard`、`/history`、`/energy`、`/map` 等任意 HA 内部路径）
- 效果：点击后在 HA 内部跳转到对应页面，无需嵌入任何外部网页。

### 示例五：仅管理员可见

- 开启「管理员可见」后，该面板只对在 HA 中拥有管理员权限的用户显示，普通用户侧边栏看不到该面板。

### 图标

- 图标使用 Material Design 图标，填写 `mdi:` 开头的名称，例如 `mdi:link-box-outline`、`mdi:node-red`、`mdi:grafana`、`mdi:chart-line`。
- 支持 `mdi-` 简写，保存时会自动转换为 `mdi:`，例如 `mdi-link-box-outline` 等效于 `mdi:link-box-outline`。

### 代理访问说明（安全）

- 代理路径与 HA 前端一样由 HA 自身鉴权保护，不再额外校验登录；请勿把敏感内网服务经由代理暴露到公网。
- 代理默认不校验上游 TLS 证书，适合内网自签名证书场景。
- 保存配置时会探测上游是否可达：任何 HTTP 响应（含 4xx/5xx）都算可达，仅连接失败 / 超时视为不可达。
- 内网访问地址示例：`http://localhost:1880/node-red/`；经代理后在 HA 域名下的访问地址类似 `http://HASS地址:8123/node-red/`。

## 如果这个项目对你有帮助，请我喝杯<del style="font-size: 14px;">咖啡</del>奶茶吧😘
|  |支付宝|微信|
|---|---|---|
奶茶= | <img src="https://github.com/shaonianzhentan/ha-docs/raw/master/docs/img/alipay.png" align="left" height="160" width="160" alt="支付宝" title="支付宝">  |  <img src="https://github.com/shaonianzhentan/ha-docs/raw/master/docs/img/wechat.png" align="left" height="160" width="160" alt="微信支付" title="微信">


#### 关注我的微信订阅号，了解更多HomeAssistant相关知识
<img src="https://github.com/shaonianzhentan/ha-docs/raw/master/docs/img/wechat-channel.png" align="left" height="160" alt="HomeAssistant家庭助理" title="HomeAssistant家庭助理"> 