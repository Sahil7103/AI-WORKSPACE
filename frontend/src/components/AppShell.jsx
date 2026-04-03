import React, { useState } from 'react'
import Sidebar from './Sidebar'
import { Menu, X } from 'lucide-react'

const AppShell = ({
  user,
  onLogout,
  children,
  contentClassName = '',
  sidebarContent,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen)

  return (
    <div className="flex h-screen w-full bg-[#18181A] text-[#F4F4F5] font-sans antialiased overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 md:hidden" 
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Wrapper */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out
        md:relative md:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <Sidebar user={user} onLogout={onLogout}>
          {sidebarContent}
        </Sidebar>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden relative">
        {/* Mobile Header (Hamburger) */}
        <div className="md:hidden flex items-center p-4 z-10 sticky top-0 bg-[#18181A]/80 backdrop-blur-sm">
          <button 
            onClick={toggleSidebar} 
            className="p-2 text-[#A1A1AA] hover:text-[#F4F4F5] rounded-lg hover:bg-[#27272A] transition-colors"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Dynamic Content */}
        <main className={`flex-1 relative overflow-auto ${contentClassName}`.trim()}>
          {children}
        </main>
      </div>
    </div>
  )
}

export default AppShell
