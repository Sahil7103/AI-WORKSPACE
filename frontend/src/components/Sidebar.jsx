import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { getInitials } from '../utils/helpers'

const Sidebar = ({ role, user, onLogout, children }) => {
  const location = useLocation()

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/'
    }

    return location.pathname.startsWith(path)
  }

  const navItems = [
    { to: '/', label: 'Home', description: 'Overview and shortcuts' },
    { to: '/chat', label: 'Chat', description: 'Conversations and answers' },
    { to: '/documents', label: 'Documents', description: 'Files and processing' },
  ]

  if (role === 'admin') {
    navItems.push({
      to: '/admin',
      label: 'Admin',
      description: 'Users and system controls',
    })
  }

  return (
    <aside className="app-sidebar">
      <div className="app-sidebar__brand">
        <div className="app-sidebar__badge">AI</div>
        <div>
          <p className="app-sidebar__title">Copilot</p>
          <p className="app-sidebar__subtitle">ChatGPT-style workspace</p>
        </div>
      </div>

      <div className="app-sidebar__scroll">
        <Link to="/chat" className="sidebar-primary-link">
          <span className="sidebar-primary-link__plus">+</span>
          <span>New chat</span>
        </Link>

        <div className="sidebar-section">
          <p className="sidebar-section__label">Workspace</p>
          <nav className="sidebar-nav">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`sidebar-nav__item ${
                  isActive(item.to) ? 'sidebar-nav__item--active' : ''
                }`.trim()}
              >
                <span className="sidebar-nav__title">{item.label}</span>
                <span className="sidebar-nav__description">{item.description}</span>
              </Link>
            ))}
          </nav>
        </div>

        {children ? (
          <div className="sidebar-section">
            <p className="sidebar-section__label">Recent chats</p>
            <div className="sidebar-stack">{children}</div>
          </div>
        ) : null}
      </div>

      {user ? (
        <div className="app-sidebar__footer">
          <div className="app-sidebar__user">
            <div className="app-sidebar__avatar">
              {getInitials(user.full_name || user.username || 'AI').slice(0, 2)}
            </div>
            <div className="app-sidebar__user-copy">
              <p className="app-sidebar__user-name">
                {user.full_name || user.username}
              </p>
              <p className="app-sidebar__user-email">{user.email}</p>
            </div>
          </div>

          <Link
            to="/login"
            onClick={onLogout}
            className="sidebar-secondary-link"
          >
            Log out
          </Link>
        </div>
      ) : null}
    </aside>
  )
}

export default Sidebar
