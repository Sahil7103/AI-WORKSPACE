import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Plus, 
  Search, 
  MessageSquare, 
  Folder, 
  ShieldAlert,
  Download
} from 'lucide-react'

import { getInitials } from '../utils/helpers'
import { chatAPI } from '../services/api'

const SidebarItem = ({ to, icon: Icon, label, isActive }) => (
  <Link
    to={to}
    className={`
      flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
      hover:bg-[#27272A] 
      ${isActive ? 'bg-[#27272A] text-[#F4F4F5]' : 'text-[#A1A1AA] hover:text-[#F4F4F5]'}
    `}
  >
    <Icon size={18} strokeWidth={2} />
    <span>{label}</span>
  </Link>
)

const Sidebar = ({ role, user, onLogout, children }) => {
  const location = useLocation()
  const [recentChats, setRecentChats] = useState([])

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  useEffect(() => {
    if (children || !user) return

    const loadChats = async () => {
      try {
        const response = await chatAPI.listSessions(0, 20)
        setRecentChats(response.data.sessions || [])
      } catch {
        setRecentChats([])
      }
    }

    loadChats()
  }, [children, user])

  const defaultChatList = recentChats.map((session) => (
    <Link
      key={session.id}
      to={`/chat/${session.id}`}
      className={`group flex items-center w-full rounded-lg text-sm px-3 py-2 transition-colors ${
        location.pathname === `/chat/${session.id}`
          ? 'bg-[#27272A] text-[#F4F4F5] font-medium'
          : 'text-[#A1A1AA] hover:bg-[#27272A] hover:text-[#F4F4F5]'
      }`}
    >
      <span className="truncate block whitespace-nowrap overflow-hidden">
        {session.session_name || 'New Chat'}
      </span>
    </Link>
  ))

  return (
    <aside className="flex flex-col h-full w-full bg-[#18181A] border-r border-[#3F3F46]/60 text-[#F4F4F5]">
      {/* Brand Header */}
      <div className="flex items-center justify-between px-4 py-3 pb-5">
        <div className="text-xl font-serif text-[#F4F4F5]">
          Sarthi
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 space-y-6">
        
        {/* Core Actions */}
        <div className="space-y-1">
          <Link
            to="/chat"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-[#F4F4F5] hover:bg-[#27272A] transition-colors text-sm font-medium"
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-sm bg-[#EA580C] text-white">
              <Plus size={16} strokeWidth={3} />
            </div>
            <span>New chat</span>
          </Link>
          
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-[#A1A1AA] hover:bg-[#27272A] hover:text-[#F4F4F5] transition-colors">
            <Search size={18} strokeWidth={2} />
            <span>Search</span>
          </button>
          
        </div>

        {/* Navigation Sections */}
        <div className="space-y-4">
          <div className="space-y-1">
            <SidebarItem 
              to="/documents" 
              icon={Folder} 
              label="Documents" 
              isActive={isActive('/documents')} 
            />
            {role === 'admin' && (
              <SidebarItem 
                to="/admin" 
                icon={ShieldAlert} 
                label="Admin" 
                isActive={isActive('/admin')} 
              />
            )}
          </div>
        </div>

        {/* Recent Threads Slot */}
        <div className="space-y-1 pt-4 border-t border-[#3F3F46]/40">
          <p className="px-3 text-xs font-semibold text-[#A1A1AA] uppercase tracking-wider mb-2">
            Chats
          </p>
          {children || defaultChatList}
        </div>
      </div>

      {/* Footer / User Profile */}
      <div className="flex items-center justify-between p-4 border-t border-[#3F3F46]/40 mt-auto">
        <button 
          onClick={onLogout}
          className="flex items-center gap-3 text-sm font-medium text-[#A1A1AA] hover:text-[#F4F4F5] transition-colors"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#27272A] text-xs font-bold text-[#F4F4F5]">
            {getInitials(user?.full_name || user?.username || 'U').slice(0, 2)}
          </div>
          <div className="text-left leading-tight hidden sm:block">
            <div className="text-[#F4F4F5]">{user?.full_name || user?.username || 'User'}</div>
            <div className="text-xs text-[#A1A1AA]">Log out</div>
          </div>
        </button>
        <button className="text-[#A1A1AA] hover:text-[#F4F4F5] p-2 rounded-md hover:bg-[#27272A] transition-colors">
          <Download size={16} />
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
