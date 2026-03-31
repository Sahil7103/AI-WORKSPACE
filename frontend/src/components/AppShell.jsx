import React from 'react'
import Header from './Header'
import Sidebar from './Sidebar'

const AppShell = ({
  user,
  onLogout,
  title,
  subtitle,
  actions,
  sidebarContent,
  children,
  contentClassName = '',
}) => {
  return (
    <div className="app-shell">
      <Sidebar role={user?.role} user={user} onLogout={onLogout}>
        {sidebarContent}
      </Sidebar>

      <div className="app-shell__main">
        <Header title={title} subtitle={subtitle} actions={actions} />
        <main className={`app-shell__content ${contentClassName}`.trim()}>
          {children}
        </main>
      </div>
    </div>
  )
}

export default AppShell
