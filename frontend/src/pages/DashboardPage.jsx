import React, { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/AppShell'
import { authAPI } from '../services/api'
import { 
  Paperclip, 
  FileText, 
  Link, 
  Mail, 
  MessageCircle, 
  GitBranch 
} from 'lucide-react'

const DashboardPage = () => {
  const [user, setUser] = useState(null)
  const [inputVal, setInputVal] = useState('')
  const [showAttachMenu, setShowAttachMenu] = useState(false)
  
  const menuRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await authAPI.getMe()
        setUser(response.data)
      } catch {
        navigate('/login')
      }
    }
    fetchUser()
  }, [navigate])

  // Close attach menu if clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowAttachMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!inputVal.trim()) return
    navigate('/chat', { state: { initialQuery: inputVal } })
  }

  if (!user) return <div className="flex items-center justify-center min-h-screen text-[#A1A1AA]">Loading workspace...</div>

  return (
    <AppShell user={user} onLogout={handleLogout}>
      <div className="flex flex-col items-center justify-center h-full w-full max-w-3xl mx-auto px-4">
        
        {/* Welcome Text */}
        <div className="flex flex-col items-center gap-4 mb-10 w-full text-center">
          <div className="flex items-center justify-center h-12 w-12 text-[#EA580C]">
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-12 h-12">
              <path d="M12 2L13.5 10.5L22 12L13.5 13.5L12 22L10.5 13.5L2 12L10.5 10.5L12 2Z" />
            </svg>
          </div>
          <h1 className="text-4xl font-serif text-[#F4F4F5] tracking-tight">
            Welcome, {user.full_name?.split(' ')[0] || user.username || 'Friend'}
          </h1>
        </div>

        {/* Composer Frame */}
        <div className="relative w-full">
          <form 
            onSubmit={handleSubmit}
            className="w-full bg-[#27272A] border border-[#3F3F46] rounded-3xl p-3 shadow-lg flex flex-col transition-shadow focus-within:shadow-xl focus-within:ring-1 focus-within:ring-[#EA580C]"
          >
            <div className="flex flex-col min-h-[80px]">
              <textarea
                className="w-full bg-transparent text-[#F4F4F5] placeholder:text-[#A1A1AA] resize-none outline-none text-lg px-2 flex-1"
                rows={2}
                placeholder="How can I help you today?"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSubmit(e)
                  }
                }}
              />
              
              <div className="flex items-center justify-between mt-2 pt-2 px-1 relative">
                {/* Attachement button relative wrapper */}
                <div className="flex items-center gap-1" ref={menuRef}>
                  <button 
                    type="button" 
                    onClick={() => setShowAttachMenu(!showAttachMenu)}
                    className={`p-2 rounded-full transition-colors ${showAttachMenu ? 'bg-[#3F3F46] text-[#F4F4F5]' : 'text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#3F3F46]'}`}
                  >
                    <Paperclip size={20} />
                  </button>

                  {/* Attachment Popover Menu */}
                  {showAttachMenu && (
                    <div className="absolute left-0 bottom-full mb-2 w-64 bg-[#27272A] border border-[#3F3F46] rounded-2xl shadow-2xl overflow-hidden z-50">
                      <div className="p-2 space-y-1">
                        <button type="button" onClick={() => {navigate('/documents'); setShowAttachMenu(false)}} className="w-full flex items-center gap-3 px-3 py-2 text-sm text-[#F4F4F5] hover:bg-[#3F3F46] rounded-xl transition-colors">
                          <FileText size={16} className="text-[#A1A1AA]" />
                          Add Document
                        </button>
                        
                        <div className="my-2 border-t border-[#3F3F46]"></div>
                        
                        <div className="px-3 py-1 text-xs font-semibold text-[#A1A1AA] uppercase tracking-wider">
                          Connectors
                        </div>
                        
                        <div className="w-full flex items-center justify-between px-3 py-2 text-sm text-[#F4F4F5] hover:bg-[#3F3F46] rounded-xl transition-colors cursor-pointer group">
                          <div className="flex items-center gap-3">
                            <Mail size={16} className="text-[#A1A1AA]" />
                            <span>Gmail</span>
                          </div>
                          <div className="w-8 h-5 bg-[#3F3F46] rounded-full flex items-center px-1 transition-colors group-hover:bg-[#52525B]">
                            <div className="w-3 h-3 bg-[#A1A1AA] rounded-full"></div>
                          </div>
                        </div>

                        <div className="w-full flex items-center justify-between px-3 py-2 text-sm text-[#F4F4F5] hover:bg-[#3F3F46] rounded-xl transition-colors cursor-pointer group">
                          <div className="flex items-center gap-3">
                            <MessageCircle size={16} className="text-[#A1A1AA]" />
                            <span>Slack</span>
                          </div>
                          <div className="w-8 h-5 bg-[#3F3F46] rounded-full flex items-center px-1 transition-colors group-hover:bg-[#52525B]">
                            <div className="w-3 h-3 bg-[#A1A1AA] rounded-full"></div>
                          </div>
                        </div>

                        <div className="w-full flex items-center justify-between px-3 py-2 text-sm text-[#F4F4F5] hover:bg-[#3F3F46] rounded-xl transition-colors cursor-pointer group">
                          <div className="flex items-center gap-3">
                            <GitBranch size={16} className="text-[#A1A1AA]" />
                            <span>Github</span>
                          </div>
                          <div className="w-8 h-5 bg-[#EA580C] rounded-full flex items-center justify-end px-1 transition-colors group-hover:bg-[#C2410C]">
                            <div className="w-3 h-3 bg-[#F4F4F5] rounded-full"></div>
                          </div>
                        </div>

                      </div>
                    </div>
                  )}
                </div>

                {/* Submit / End actions can go here if needed. 
                    Model selector was removed per request. */}
                <div className="flex items-center gap-2">
                  {/* Empty right side. Submit button could go here or the user just hits Enter */}
                </div>
              </div>
            </div>
          </form>
        </div>

      </div>
    </AppShell>
  )
}

export default DashboardPage
