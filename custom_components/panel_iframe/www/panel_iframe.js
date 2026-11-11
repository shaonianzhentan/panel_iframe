// 新版 Home Assistant 不再保证向自定义面板暴露 LitElement.prototype.html/css，
// 因此这里使用标准 HTMLElement + Shadow DOM，不依赖前端内部实现。
const PANEL_TAG = 'ha-panel_iframe'

const STYLES = `
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
  box-sizing: border-box;
  background-color: var(--app-header-background-color);
  color: var(--app-header-text-color, #fff);
  border-bottom: var(--app-header-border-bottom, none);
  font-weight: 400;
}
@media (max-width: 599px) {
  .toolbar { padding: 4px; }
}
.main-title {
  margin: 0 0 0 12px;
  line-height: 20px;
  flex-grow: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.content {
  position: relative;
  width: 100%;
  height: calc(100% - 1px - var(--header-height));
}
iframe { border: none; width: 100%; height: 100%; }
button.menu-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
}
button.menu-button[hidden] { display: none; }
button.menu-button svg { width: 24px; height: 24px; fill: currentColor; }
.nav-button {
  position: fixed;
  bottom: calc(16px + env(safe-area-inset-bottom));
  right: calc(16px + env(safe-area-inset-right));
  z-index: 1;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: var(--text-primary-color, #fff);
  box-shadow: 0 2px 6px rgba(0, 0, 0, .3);
}
.external, .empty {
  box-sizing: border-box;
  width: 100%;
  height: calc(100% - 1px - var(--header-height));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  text-align: center;
  word-break: break-all;
}
.external a { color: var(--primary-color); }
`

const MENU_ICON =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z"/></svg>'

class PanelIframe extends HTMLElement {
  constructor() {
    super()
    this._hass = undefined
    this._narrow = false
    this._panel = undefined
    this._menuButton = null
    this._signature = undefined
    this._openedUrl = undefined
    this.attachShadow({ mode: 'open' })
  }

  get hass() { return this._hass }
  set hass(value) {
    // hass 会随 HA 状态频繁变化，只保存不重绘，避免 iframe 反复刷新
    this._hass = value
  }

  get narrow() { return this._narrow }
  set narrow(value) {
    this._narrow = Boolean(value)
    this.toggleAttribute('narrow', this._narrow)
    this._syncMenuButton()
  }

  get panel() { return this._panel }
  set panel(value) {
    this._panel = value
    this._render()
  }

  connectedCallback() {
    // 属性有可能在自定义元素升级之前被写入，需要重新经过 setter
    for (const name of ['hass', 'narrow', 'panel']) {
      if (Object.prototype.hasOwnProperty.call(this, name)) {
        const value = this[name]
        delete this[name]
        this[name] = value
      }
    }
    this._render()
  }

  _fire(type, detail) {
    this.dispatchEvent(
      new CustomEvent(type, { bubbles: true, composed: true, detail })
    )
  }

  _resolveUrl(value) {
    let url = String(value == null ? '' : value).trim()
    if (/^\d+$/.test(url)) {
      url = 'http://' + location.hostname + ':' + url
    } else if (url.startsWith('//')) {
      url = location.protocol + '//' + location.hostname + url.substring(1)
    } else if (url.startsWith(':')) {
      url = location.protocol + '//' + location.hostname + url
    }
    return url
  }

  _reset(title, withToolbar = true) {
    this.shadowRoot.innerHTML = `<style>${STYLES}</style>`
    this._menuButton = null
    if (!withToolbar) {
      const floating = this._createMenuButton(true)
      this.shadowRoot.appendChild(floating)
      this._menuButton = floating
      this._syncMenuButton()
      return
    }
    const toolbar = document.createElement('div')
    toolbar.className = 'toolbar'
    const menu = this._createMenuButton(false)
    toolbar.appendChild(menu)
    const label = document.createElement('div')
    label.className = 'main-title'
    label.textContent = title || ''
    toolbar.appendChild(label)
    this.shadowRoot.appendChild(toolbar)
    this._menuButton = menu
    this._syncMenuButton()
  }

  _createMenuButton(floating) {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = floating ? 'menu-button nav-button' : 'menu-button'
    button.title = '菜单'
    button.setAttribute('aria-label', '打开侧边栏')
    button.innerHTML = MENU_ICON
    button.addEventListener('click', (event) => {
      event.stopPropagation()
      this._fire('hass-toggle-menu')
    })
    return button
  }

  _syncMenuButton() {
    if (this._menuButton) this._menuButton.hidden = !this._narrow
  }

  _addIframe(url) {
    const iframe = document.createElement('iframe')
    iframe.setAttribute('allow', 'fullscreen')
    iframe.src = url
    return iframe
  }

  _renderEmbedded(url, title, mode) {
    this._reset(title)
    const content = document.createElement('div')
    content.className = 'content'
    const jump = '/panel_iframe_www/index.html?mode=' +
      encodeURIComponent(mode == null ? '' : mode) +
      '&url=' + encodeURIComponent(url)
    content.appendChild(this._addIframe(jump))
    this.shadowRoot.appendChild(content)
  }

  _renderFullscreen(url, title) {
    this._reset(title, false)
    const iframe = this._addIframe(url)
    iframe.style.height = '100vh'
    this.shadowRoot.appendChild(iframe)
  }

  _renderExternal(url, title) {
    this._reset(title)
    if (this._openedUrl !== url) {
      this._openedUrl = url
      window.open(url, '_blank', 'noopener')
    }
    const box = document.createElement('div')
    box.className = 'external'
    const text = document.createElement('span')
    text.textContent = '已在新窗口打开，如果窗口被拦截，请点击下面的链接：'
    const link = document.createElement('a')
    link.href = url
    link.target = '_blank'
    link.rel = 'noopener noreferrer'
    link.textContent = url
    box.append(text, link)
    this.shadowRoot.appendChild(box)
  }

  _renderEmpty(title) {
    this._reset(title)
    const box = document.createElement('div')
    box.className = 'empty'
    box.textContent = '请先在集成选项中配置链接地址'
    this.shadowRoot.appendChild(box)
  }

  _render() {
    const panel = this._panel
    if (!panel) return
    const config = panel.config || {}
    const title = panel.title || ''
    const mode = config.mode
    const signature = JSON.stringify([title, mode, config.url])
    if (signature === this._signature) return
    this._signature = signature

    const url = this._resolveUrl(config.url)
    if (mode == 3) {
      // 保留 HA 写入 history.state 的路由/dialog 数据，不能置空
      window.history.replaceState(window.history.state, '', url)
      this._fire('location-changed', { replace: true })
      this.shadowRoot.innerHTML = ''
      return
    }

    if (!url) {
      this._renderEmpty(title)
      return
    }

    const mixedContent = location.protocol === 'https:' && url.startsWith('http://')
    if (mode == 2 || mixedContent) {
      this._renderExternal(url, title)
    } else if (mode == 1) {
      this._renderFullscreen(url, title)
    } else {
      this._renderEmbedded(url, title, mode)
    }
  }
}

if (!customElements.get(PANEL_TAG)) {
  customElements.define(PANEL_TAG, PanelIframe)
}
