import React from 'react'

const Header = ({ title, subtitle, actions }) => {
  return (
    <header className="app-header">
      <div className="app-header__copy">
        <p className="app-header__eyebrow">AI Workplace Copilot</p>
        <h1 className="app-header__title">{title}</h1>
        {subtitle ? <p className="app-header__subtitle">{subtitle}</p> : null}
      </div>

      {actions ? <div className="app-header__actions">{actions}</div> : null}
    </header>
  )
}

export default Header
