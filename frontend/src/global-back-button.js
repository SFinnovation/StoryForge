(() => {
  const currentScript = document.currentScript

  const createBackButton = () => {
    if (document.querySelector('[data-sf-global-back-button]')) return

    const fallbackUrl = currentScript?.dataset?.fallback || ''
    const label = currentScript?.dataset?.label || '返回上一个界面'
    const button = document.createElement('button')
    const icon = document.createElement('span')

    button.type = 'button'
    button.className = 'sf-global-back-button'
    if (document.querySelector('.navbar')) {
      button.classList.add('sf-global-back-button--below-navbar')
    }
    button.dataset.sfGlobalBackButton = ''
    button.setAttribute('aria-label', label)
    button.setAttribute('title', label)

    icon.className = 'sf-global-back-button__icon'
    icon.setAttribute('aria-hidden', 'true')
    button.appendChild(icon)

    button.addEventListener('click', () => {
      if (window.history.length > 1) {
        window.history.back()
        return
      }

      if (fallbackUrl) {
        window.location.href = fallbackUrl
      }
    })

    document.body.appendChild(button)
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createBackButton, { once: true })
  } else {
    createBackButton()
  }
})()
