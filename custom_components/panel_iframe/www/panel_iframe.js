customElements.whenDefined('ha-panel-lovelace').then(() => {
  const LitElement = Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
  const html = LitElement.prototype.html;
  const css = LitElement.prototype.css;

  customElements.define('ha-panel_iframe', class extends LitElement {

    static properties = {
      panel: {},
      hass: {},
      narrow: {}
    };

    constructor() {
      super();
    }

    static styles = css`
    :host {
      display: block;
      height: 100%;
      background-color: var(--primary-background-color);
      overflow: hidden;
      position: relative;
    }

    :host([narrow]) {
      width: 100%;
      position: fixed;
    }

    .toolbar {
      display: flex;
      align-items: center;
      font-size: 20px;
      height: var(--header-height);
      padding: 8px 12px;
      pointer-events: none;
      background-color: var(--app-header-background-color);
      font-weight: 400;
      color: var(--app-header-text-color, white);
      border-bottom: var(--app-header-border-bottom, none);
      box-sizing: border-box;
    }
    @media (max-width: 599px) {
      .toolbar {
        padding: 4px;
      }
    }
    .toolbar a {
      color: var(--sidebar-text-color);
      text-decoration: none;
    }

    ha-menu-button,
    ha-icon-button-arrow-prev,
    ::slotted([slot="toolbar-icon"]) {
      pointer-events: auto;
    }

    .main-title {
      margin: 0 0 0 24px;
      line-height: 20px;
      flex-grow: 1;
    }

    .content {
      position: relative;
      width: 100%;
      height: calc(100% - 1px - var(--header-height));
    }

    #fab {
      position: absolute;
      right: calc(16px + env(safe-area-inset-right));
      bottom: calc(16px + env(safe-area-inset-bottom));
      z-index: 1;
    }
    :host([narrow]) #fab.tabs {
      bottom: calc(84px + env(safe-area-inset-bottom));
    }
    #fab[is-wide] {
      bottom: 24px;
      right: 24px;
    }
    :host([rtl]) #fab {
      right: auto;
      left: calc(16px + env(safe-area-inset-left));
    }
    :host([rtl][is-wide]) #fab {
      bottom: 24px;
      left: 24px;
      right: auto;
    }

    iframe{border:none;width:100%;height:100%;}
    .nav-button{
      position:fixed;
      bottom:5px;
      right: 5px;
    }`;

    fireEvent(type, data) {
      const event = new Event(type, {
        bubbles: true,
        cancelable: false,
        composed: true
      });
      event.detail = data;
      this.dispatchEvent(event);
    }

    _toggleMenu(event) {
      this.fireEvent('hass-toggle-menu')
      event.stopPropagation()
    }

    render() {
      const { config, title } = this.panel
      let { url, mode } = config
      // 如果传入的是端口号
      if (/^\d+$/.test(url)) {
        url = 'http://' + location.hostname + ':' + url
      }
      // 如果传入的双斜杠，则忽略默认端口
      if (url.indexOf('//') == 0) {
        url = location.protocol + '//' + location.hostname + url.substring(1)
      }
      // 如果传入端口路径
      if (url.indexOf(':') == 0) {
        url = location.protocol + '//' + location.hostname + url
      }
      // 内置页面
      if (mode == 3) {
        history.replaceState(null, null, url)
        return this.fireEvent('location-changed', { replace: true })
      }
      // 如果HTTPS协议，则打开新页面
      if (location.protocol === 'https:' && url.indexOf('http://') == 0) {
        
      } else {
        // 全屏显示
        if (mode == 1) {
          return html`<iframe allow="fullscreen" src="${url}" style="height:100vh;"></iframe>
            ${this.narrow ? html`<ha-icon-button class="nav-button" @click=${this._toggleMenu.bind(this)}><ha-icon icon="mdi:home-assistant"></ha-icon></ha-icon-button>` : ''}`
        }
      }
      // 内置显示
      return html`<div class="toolbar">
          <ha-menu-button
            .hass=${this.hass}
            .narrow=${this.narrow}
          ></ha-menu-button>
          <div class="main-title"><slot name="header">${title}</slot></div>
          <slot name="toolbar-icon"></slot>
        </div>
        <div class="content ha-scrollbar">
          <iframe allow="fullscreen" src="/panel_iframe_www/index.html?mode=${mode}&url=${encodeURIComponent(url)}"></iframe>
        </div>
      `;
    }
  });
})