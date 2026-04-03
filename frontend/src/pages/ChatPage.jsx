import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppShell from '../components/AppShell'
import ChatMessage from '../components/ChatMessage'
import { authAPI, chatAPI } from '../services/api'
import { 
  Paperclip, 
  Send,
  FileText,
  Mail,
  MessageCircle,
  GitBranch,
  MoreHorizontal,
  Pencil,
  Trash2,
  Check,
  X,
  MessageSquare
} from 'lucide-react'

const normalizeSources = (sources) => {
  if (!sources) return []
  if (Array.isArray(sources)) return sources
  if (typeof sources === 'string') {
    try {
      const parsed = JSON.parse(sources)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
}

const normalizeMessage = (message) => ({
  ...message,
  sources: normalizeSources(message.sources),
})

const ChatPage = () => {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  
  const [user, setUser] = useState(null)
  const [sessions, setSessions] = useState([])
  const [currentSession, setCurrentSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState(location.state?.initialQuery || '')
  const [loading, setLoading] = useState(false)
  const [showAttachMenu, setShowAttachMenu] = useState(false)
  
  // Sidebar Thread Context Menus
  const [editingSessionId, setEditingSessionId] = useState(null)
  const [editSessionName, setEditSessionName] = useState('')
  const [openMenuId, setOpenMenuId] = useState(null)
  
  const messagesEndRef = useRef(null)
  const menuRef = useRef(null)
  const threadMenuRefs = useRef({})
  const composerTextareaRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const textarea = composerTextareaRef.current
    if (!textarea) return

    textarea.style.height = '0px'
    const nextHeight = Math.min(textarea.scrollHeight, 160)
    textarea.style.height = `${Math.max(nextHeight, 28)}px`
  }, [input])

  // Close attach menu if clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowAttachMenu(false)
      }
      
      // Close thread options menu if clicking outside
      if (openMenuId !== null) {
        const ref = threadMenuRefs.current[openMenuId]
        if (ref && !ref.contains(event.target)) {
          setOpenMenuId(null)
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [openMenuId])

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
    const fetchSessions = async () => {
      try {
        const response = await chatAPI.listSessions()
        setSessions(response.data.sessions || [])
      } catch {
        toast.error('Failed to load sessions')
      }
    }
    fetchSessions()
  }, [])

  useEffect(() => {
    if (!sessionId) {
      setCurrentSession(null)
      setMessages([])
      
      if (location.state?.initialQuery) {
        handleNewSession(location.state.initialQuery)
        navigate('/chat', { replace: true, state: {} })
      }
      return
    }

    const fetchSession = async () => {
      try {
        const response = await chatAPI.getSession(sessionId)
        setCurrentSession(response.data)
        setMessages((response.data.messages || []).map(normalizeMessage))
      } catch {
        toast.error('Failed to load session')
      }
    }
    fetchSession()
  }, [sessionId, location.state])

  // Helpers for Thread operations
  const handleRenameSubmit = async (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    if (!editSessionName.trim()) {
       setEditingSessionId(null)
       return
    }
    try {
       await chatAPI.renameSession(id, editSessionName)
       setSessions(prev => prev.map(s => s.id === id ? { ...s, session_name: editSessionName } : s))
       if (currentSession?.id === id) {
          setCurrentSession(prev => ({ ...prev, session_name: editSessionName }))
       }
       toast.success('Chat renamed')
    } catch {
       toast.error('Could not rename via API, updating locally')
       setSessions(prev => prev.map(s => s.id === id ? { ...s, session_name: editSessionName } : s))
    }
    setEditingSessionId(null)
  }

  const handleDeleteSession = async (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await chatAPI.deleteSession(id)
      setSessions(prev => prev.filter(s => s.id !== id))
      toast.success('Chat deleted')
      if (sessionId === String(id)) {
        navigate('/chat')
      }
    } catch {
      toast.error('Failed to delete chat')
    }
    setOpenMenuId(null)
  }

  const handleNewSession = async (initialMessage = '') => {
    try {
      const response = await chatAPI.createSession('New Chat')
      const finalSession = { ...response.data, session_name: response.data.session_name || 'New Chat' }
      
      setSessions((prev) => [finalSession, ...prev])
      navigate(`/chat/${finalSession.id}`)
      
      if (initialMessage && typeof initialMessage === 'string') {
        setTimeout(() => sendMessage(initialMessage, finalSession.id), 100)
      }
    } catch {
      toast.error('Failed to create session')
    }
  }

  const sendMessage = async (messageContent, targetSessionId) => {
    if (!messageContent.trim()) return

    const nextInput = messageContent.trim()
    const optimisticUserMessage = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: nextInput,
      created_at: new Date().toISOString(),
      sources: [],
    }
    const streamingAssistantMessageId = `temp-assistant-${Date.now()}`
    const optimisticAssistantMessage = {
      id: streamingAssistantMessageId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      sources: [],
      streaming: true,
    }

    setMessages((prev) => [...prev, optimisticUserMessage, optimisticAssistantMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatAPI.queryStream({
        session_id: parseInt(targetSessionId, 10),
        query: nextInput,
      }, {
        onToken: (_, fullText) => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === streamingAssistantMessageId
                ? { ...message, content: fullText }
                : message
            )
          )
        },
      })

      if (response.session_name) {
        setSessions((prev) =>
          prev.map((session) =>
            session.id === parseInt(targetSessionId, 10)
              ? { ...session, session_name: response.session_name }
              : session
          )
        )
        setCurrentSession((prev) =>
          prev && prev.id === parseInt(targetSessionId, 10)
            ? { ...prev, session_name: response.session_name }
            : prev
        )
      }

      setMessages((prev) =>
        prev.map((message) =>
          message.id === streamingAssistantMessageId
            ? {
                ...message,
                id: response.message_id || message.id,
                content: response.response || message.content,
                streaming: false,
              }
            : message
        )
      )
    } catch {
      setMessages((prev) =>
        prev.filter(
          (m) => m.id !== optimisticUserMessage.id && m.id !== streamingAssistantMessageId
        )
      )
      setInput(nextInput)
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = (e) => {
    e.preventDefault()
    if (!sessionId) {
      handleNewSession(input)
    } else {
      sendMessage(input, sessionId)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(e)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  if (!user) return <div className="flex h-screen items-center justify-center text-[#A1A1AA]">Loading chat...</div>

  // Render Sidebar Content for Threads
  const sidebarThreadsList = sessions.map(session => (
    <div 
      key={session.id} 
      className={`group relative flex items-center justify-between w-full rounded-lg text-sm px-2 py-1.5 transition-colors cursor-pointer ${String(session.id) === sessionId ? 'bg-[#27272A] text-[#F4F4F5] font-medium' : 'text-[#A1A1AA] hover:bg-[#27272A] hover:text-[#F4F4F5] font-medium'}`}
      onClick={() => { if (editingSessionId !== session.id) navigate(`/chat/${session.id}`) }}
    >
      <div className="flex items-center gap-2 overflow-hidden flex-1 pl-1">
        {editingSessionId === session.id ? (
          <form 
            onSubmit={(e) => handleRenameSubmit(e, session.id)} 
            className="flex items-center w-full gap-1 z-20 bg-[#27272A] px-1 -ml-1 rounded" 
            onClick={e => e.stopPropagation()}
          >
            <input 
              autoFocus
              className="w-full bg-transparent border-none text-[#F4F4F5] outline-none text-sm p-0 m-0"
              value={editSessionName}
              onChange={(e) => setEditSessionName(e.target.value)}
              onBlur={(e) => handleRenameSubmit(e, session.id)}
            />
          </form>
        ) : (
          <span className="truncate block whitespace-nowrap overflow-hidden pr-6">
            {session.session_name || 'New Chat'}
          </span>
        )}
      </div>

      {editingSessionId !== session.id && (
        <div 
          className={`absolute right-1 top-1/2 -translate-y-1/2 transition-opacity flex items-center ${openMenuId === session.id ? 'opacity-100 z-50' : 'opacity-0 group-hover:opacity-100'}`}
          ref={el => threadMenuRefs.current[session.id] = el}
          onClick={e => e.stopPropagation()}
        >
          <button 
            type="button" 
            onClick={(e) => {
              e.stopPropagation()
              setOpenMenuId(openMenuId === session.id ? null : session.id)
            }}
            className="p-1 rounded-md text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#3F3F46] transition-colors"
          >
            <MoreHorizontal size={14} />
          </button>
          
          {openMenuId === session.id && (
            <div className="absolute right-0 mt-1 w-32 bg-[#27272A] border border-[#3F3F46] rounded-xl shadow-xl overflow-hidden z-50 py-1">
              <button 
                onClick={(e) => {
                  e.stopPropagation()
                  setEditSessionName(session.session_name || 'New Chat')
                  setEditingSessionId(session.id)
                  setOpenMenuId(null)
                }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#F4F4F5] hover:bg-[#3F3F46] transition-colors"
              >
                <Pencil size={12} /> Rename
              </button>
              <button 
                onClick={(e) => handleDeleteSession(e, session.id)}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#EF4444] hover:bg-[#EF4444]/10 transition-colors"
              >
                <Trash2 size={12} /> Delete
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  ))

  return (
    <AppShell 
      user={user} 
      onLogout={handleLogout} 
      contentClassName="flex flex-col h-full bg-[#18181A]"
      sidebarContent={sidebarThreadsList}
    >
      <div className="flex-1 flex justify-center w-full px-4 overflow-y-auto">
        <div className="w-full max-w-3xl pb-52 pt-8 flex flex-col gap-6">
          {messages.length === 0 ? (
            <div className="flex flex-col pt-20 pb-10">
              <h2 className="text-2xl font-semibold text-[#F4F4F5]">Start a conversation</h2>
              <p className="text-[#A1A1AA] mt-2">Chat with your models about knowledge or general queries.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} user={user} />
              ))}
              {loading && !messages.some((message) => message.streaming) && (
                <div className="flex gap-4 p-2 animate-pulse">
                  <div className="w-6 h-6 rounded bg-[#27272A]" />
                  <div className="h-4 bg-[#27272A] rounded w-1/3" />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Floating Composer */}
      <div className="absolute bottom-0 left-0 right-0 px-4 pb-3 pt-7 bg-gradient-to-t from-[#18181A] via-[#18181A]/94 to-transparent flex justify-center">
        <div className="w-full max-w-3xl relative">
          
          <form 
            onSubmit={handleSendMessage}
            className="flex flex-col bg-[#27272A] border border-[#3F3F46] rounded-[1.55rem] px-3 py-2 shadow-lg focus-within:ring-1 focus-within:ring-[#EA580C] transition-shadow relative"
          >
            <div className="flex items-end bg-transparent relative">
              
              {/* Attachment Button & Menu Wrapper */}
              <div className="flex items-center gap-2 px-1 pb-0.5" ref={menuRef}>
                <button 
                  type="button" 
                  onClick={() => setShowAttachMenu(!showAttachMenu)}
                  className={`p-2 rounded-full transition-colors ${showAttachMenu ? 'bg-[#3F3F46] text-[#F4F4F5]' : 'text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#3F3F46]'}`}
                >
                  <Paperclip size={18} />
                </button>

                {/* Attachment Popover Menu */}
                {showAttachMenu && (
                  <div className="absolute left-0 bottom-[120%] mb-2 w-64 bg-[#27272A] border border-[#3F3F46] rounded-2xl shadow-2xl overflow-hidden z-[100]">
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

              <textarea
                ref={composerTextareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Reply to Copilot..."
                className="w-full bg-transparent text-[#F4F4F5] placeholder:text-[#A1A1AA] resize-none overflow-y-auto outline-none min-h-[24px] max-h-[120px] text-[15px] leading-6 px-2 py-1"
                rows={1}
              />

              <div className="flex items-end px-1 pb-0.5 gap-2 w-auto">
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="flex h-9 w-9 items-center justify-center rounded-full bg-[#EA580C] text-white hover:bg-[#C2410C] disabled:opacity-50 disabled:bg-[#3F3F46] disabled:text-[#A1A1AA] transition-colors"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </form>
          <div className="text-center mt-2 px-2 text-xs text-[#A1A1AA]">
            Claude handles frontend aesthetics. Your API remains secure.
          </div>
        </div>
      </div>
    </AppShell>
  )
}

export default ChatPage
