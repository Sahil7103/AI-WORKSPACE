import React, { useEffect, useState, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppShell from '../components/AppShell'
import { authAPI, integrationsAPI } from '../services/api'
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
  const [gmailStatus, setGmailStatus] = useState({ connected: false, imported_count: 0 })
  const [githubStatus, setGitHubStatus] = useState({ connected: false, imported_count: 0 })
  const [gmailBusy, setGmailBusy] = useState(false)
  const [githubBusy, setGitHubBusy] = useState(false)
  
  const menuRef = useRef(null)
  const navigate = useNavigate()
  const location = useLocation()

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

  useEffect(() => {
    const loadIntegrationStatus = async () => {
      try {
        const [gmailResponse, githubResponse] = await Promise.all([
          integrationsAPI.getGmailStatus(),
          integrationsAPI.getGitHubStatus(),
        ])
        setGmailStatus(gmailResponse.data)
        setGitHubStatus(githubResponse.data)
      } catch {
        setGmailStatus({ connected: false, imported_count: 0 })
        setGitHubStatus({ connected: false, imported_count: 0 })
      }
    }

    loadIntegrationStatus()
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const gmail = params.get('gmail')
    const gmailMessage = params.get('gmail_message')
    const github = params.get('github')
    const githubMessage = params.get('github_message')

    if (!gmail && !github) return

    const loadIntegrationStatus = async () => {
      try {
        const [gmailResponse, githubResponse] = await Promise.all([
          integrationsAPI.getGmailStatus(),
          integrationsAPI.getGitHubStatus(),
        ])
        setGmailStatus(gmailResponse.data)
        setGitHubStatus(githubResponse.data)
      } catch {
        setGmailStatus({ connected: false, imported_count: 0 })
        setGitHubStatus({ connected: false, imported_count: 0 })
      }
    }

    if (gmail === 'connected') {
      toast.success('Gmail connected successfully')
      loadIntegrationStatus()
    } else if (gmail === 'error') {
      toast.error(gmailMessage || 'Failed to connect Gmail')
    }

    if (github === 'connected') {
      toast.success('GitHub connected successfully')
      loadIntegrationStatus()
    } else if (github === 'error') {
      toast.error(githubMessage || 'Failed to connect GitHub')
    }

    const cleaned = `${location.pathname}${location.hash || ''}`
    window.history.replaceState({}, '', cleaned)
  }, [location.pathname, location.search, location.hash])

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

  const handleSyncGmail = async () => {
    setGmailBusy(true)
    try {
      const response = await integrationsAPI.syncGmail(20)
      setGmailStatus(response.data)
      toast.success(`Synced Gmail. Imported ${response.data.imported_count} new emails.`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sync Gmail')
    } finally {
      setGmailBusy(false)
    }
  }

  const handleDisconnectGmail = async () => {
    setGmailBusy(true)
    try {
      await integrationsAPI.disconnectGmail()
      setGmailStatus({ connected: false, imported_count: 0 })
      toast.success('Gmail disconnected')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to disconnect Gmail')
    } finally {
      setGmailBusy(false)
    }
  }

  const handleGmailToggle = async () => {
    if (gmailStatus?.connected) {
      await handleDisconnectGmail()
      return
    }

    setGmailBusy(true)
    try {
      const response = await integrationsAPI.getGmailOAuthUrl('/')
      window.location.href = response.data.auth_url
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start Gmail connection')
      setGmailBusy(false)
    }
  }

  const handleSyncGitHub = async () => {
    setGitHubBusy(true)
    try {
      const response = await integrationsAPI.syncGitHub(10)
      setGitHubStatus(response.data)
      toast.success(`Synced GitHub. Imported ${response.data.imported_count} repositories.`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sync GitHub')
    } finally {
      setGitHubBusy(false)
    }
  }

  const handleDisconnectGitHub = async () => {
    setGitHubBusy(true)
    try {
      await integrationsAPI.disconnectGitHub()
      setGitHubStatus({ connected: false, imported_count: 0 })
      toast.success('GitHub disconnected')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to disconnect GitHub')
    } finally {
      setGitHubBusy(false)
    }
  }

  const handleGitHubToggle = async () => {
    if (githubStatus?.connected) {
      await handleDisconnectGitHub()
      return
    }

    setGitHubBusy(true)
    try {
      const response = await integrationsAPI.getGitHubOAuthUrl('/')
      window.location.href = response.data.auth_url
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start GitHub connection')
      setGitHubBusy(false)
    }
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
                        
                        <button
                          type="button"
                          onClick={handleGmailToggle}
                          disabled={gmailBusy}
                          className="w-full flex items-center justify-between px-3 py-2 text-sm text-[#F4F4F5] hover:bg-[#3F3F46] rounded-xl transition-colors cursor-pointer group"
                        >
                          <div className="flex items-center gap-3">
                            <Mail size={16} className="text-[#A1A1AA]" />
                            <span>Gmail</span>
                          </div>
                          <div className={`w-8 h-5 rounded-full flex items-center px-1 transition-colors ${gmailStatus?.connected ? 'bg-[#EA580C] justify-end' : 'bg-[#3F3F46] group-hover:bg-[#52525B]'}`}>
                            <div className={`w-3 h-3 rounded-full ${gmailStatus?.connected ? 'bg-[#F4F4F5]' : 'bg-[#A1A1AA]'}`}></div>
                          </div>
                        </button>

                        <div className="w-full flex items-center justify-between px-3 py-2 text-sm text-[#F4F4F5] hover:bg-[#3F3F46] rounded-xl transition-colors cursor-pointer group">
                          <div className="flex items-center gap-3">
                            <MessageCircle size={16} className="text-[#A1A1AA]" />
                            <span>Slack</span>
                          </div>
                          <div className="w-8 h-5 bg-[#3F3F46] rounded-full flex items-center px-1 transition-colors group-hover:bg-[#52525B]">
                            <div className="w-3 h-3 bg-[#A1A1AA] rounded-full"></div>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={handleGitHubToggle}
                          disabled={githubBusy}
                          className="w-full flex items-center justify-between px-3 py-2 text-sm text-[#F4F4F5] hover:bg-[#3F3F46] rounded-xl transition-colors cursor-pointer group"
                        >
                          <div className="flex items-center gap-3">
                            <GitBranch size={16} className="text-[#A1A1AA]" />
                            <span>GitHub</span>
                          </div>
                          <div className={`w-8 h-5 rounded-full flex items-center px-1 transition-colors ${githubStatus?.connected ? 'bg-[#EA580C] justify-end' : 'bg-[#3F3F46] group-hover:bg-[#52525B]'}`}>
                            <div className={`w-3 h-3 rounded-full ${githubStatus?.connected ? 'bg-[#F4F4F5]' : 'bg-[#A1A1AA]'}`}></div>
                          </div>
                        </button>

                        {githubStatus?.connected && (
                          <button
                            type="button"
                            onClick={handleSyncGitHub}
                            disabled={githubBusy}
                            className="w-full flex items-center gap-3 px-3 py-2 text-sm text-[#F4F4F5] hover:bg-[#3F3F46] rounded-xl transition-colors"
                          >
                            <Link size={16} className="text-[#A1A1AA]" />
                            <span>{githubBusy ? 'Syncing GitHub...' : 'Sync GitHub repositories'}</span>
                          </button>
                        )}

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
