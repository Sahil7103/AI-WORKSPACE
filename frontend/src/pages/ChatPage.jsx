import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppShell from '../components/AppShell'
import ChatMessage from '../components/ChatMessage'
import { authAPI, chatAPI } from '../services/api'

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
  const [user, setUser] = useState(null)
  const [sessions, setSessions] = useState([])
  const [currentSession, setCurrentSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

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
  }, [sessionId])

  const handleNewSession = async () => {
    try {
      const response = await chatAPI.createSession('New chat')
      setSessions((prev) => [response.data, ...prev])
      navigate(`/chat/${response.data.id}`)
    } catch {
      toast.error('Failed to create session')
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || !sessionId) return

    const nextInput = input.trim()
    const optimisticUserMessage = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: nextInput,
      created_at: new Date().toISOString(),
      sources: [],
    }

    setMessages((prev) => [...prev, optimisticUserMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatAPI.query({
        session_id: parseInt(sessionId, 10),
        query: nextInput,
      })

      const assistantMessage = {
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.response,
        created_at: new Date().toISOString(),
        sources: normalizeSources(response.data.sources),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch {
      setMessages((prev) =>
        prev.filter((message) => message.id !== optimisticUserMessage.id)
      )
      setInput(nextInput)
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  if (!user) return <div className="page-loading">Loading chat...</div>

  return (
    <AppShell
      user={user}
      onLogout={handleLogout}
      title={currentSession?.session_name || 'Chat'}
      subtitle="A ChatGPT-style conversation area with recent threads in the sidebar and a focused composer."
      contentClassName="chat-shell"
      sidebarContent={sessions.map((session) => (
        <button
          key={session.id}
          onClick={() => navigate(`/chat/${session.id}`)}
          className={`sidebar-thread ${
            currentSession?.id === session.id ? 'sidebar-thread--active' : ''
          }`.trim()}
        >
          <span className="sidebar-thread__title">
            {session.session_name || 'New chat'}
          </span>
          <span className="sidebar-thread__meta">Open thread</span>
        </button>
      ))}
      actions={
        <button onClick={handleNewSession} className="btn btn-primary">
          New chat
        </button>
      }
    >
      {currentSession ? (
        <section className="chat-room">
          <div className="chat-room__messages">
            {messages.length === 0 ? (
              <div className="empty-state empty-state--chat">
                <h3 className="empty-state__title">Start the conversation</h3>
                <p className="empty-state__text">
                  Ask a question about your uploaded documents and the assistant will respond here.
                </p>
              </div>
            ) : (
              <div className="chat-room__stack">
                {messages.map((message, index) => (
                  <ChatMessage
                    key={message.id || `${message.role}-${index}`}
                    message={message}
                  />
                ))}
              </div>
            )}
          </div>

          <form onSubmit={handleSendMessage} className="composer">
            <div className="composer__inner">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message Copilot..."
                className="composer__input"
                rows={1}
              />
              <button
                type="submit"
                disabled={loading || !sessionId}
                className="btn btn-primary"
              >
                {loading ? 'Sending...' : 'Send'}
              </button>
            </div>
            <p className="composer__hint">
              Backend routes stay the same. This update is strictly a frontend redesign.
            </p>
          </form>
        </section>
      ) : (
        <section className="empty-state empty-state--chat-home">
          <h2 className="empty-state__title">No chat selected</h2>
          <p className="empty-state__text">
            Create a new conversation to start using the ChatGPT-style chat interface.
          </p>
          <button onClick={handleNewSession} className="btn btn-primary">
            Create new chat
          </button>
        </section>
      )}
    </AppShell>
  )
}

export default ChatPage
