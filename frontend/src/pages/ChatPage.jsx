import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import { authAPI, chatAPI } from '../services/api'

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
        setSessions(response.data.sessions)
      } catch (error) {
        toast.error('Failed to load sessions')
      }
    }
    fetchSessions()
  }, [])

  useEffect(() => {
    if (sessionId) {
      const fetchSession = async () => {
        try {
          const response = await chatAPI.getSession(sessionId)
          setCurrentSession(response.data)
          setMessages(response.data.messages)
        } catch (error) {
          toast.error('Failed to load session')
        }
      }
      fetchSession()
    }
  }, [sessionId])

  const handleNewSession = async () => {
    try {
      const response = await chatAPI.createSession('New Chat')
      setSessions([...sessions, response.data])
      navigate(`/chat/${response.data.id}`)
    } catch (error) {
      toast.error('Failed to create session')
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || !sessionId) return

    setLoading(true)
    try {
      const response = await chatAPI.query({
        session_id: parseInt(sessionId),
        query: input,
      })

      setMessages([...messages, response.data])
      setInput('')
      toast.success('Message sent!')
    } catch (error) {
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  if (!user) return <div>Loading...</div>

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar role={user.role} />
      <div className="flex-1 flex flex-col">
        <Header user={user} onLogout={handleLogout} />

        <div className="flex flex-1 overflow-hidden">
          {/* Sessions Sidebar */}
          <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
            <div className="p-4">
              <button
                onClick={handleNewSession}
                className="btn btn-primary w-full mb-4"
              >
                + New Chat
              </button>

              <div className="space-y-2">
                {sessions.map((session) => (
                  <button
                    key={session.id}
                    onClick={() => navigate(`/chat/${session.id}`)}
                    className={`w-full text-left px-4 py-2 rounded-lg transition ${
                      currentSession?.id === session.id
                        ? 'bg-blue-100 text-blue-900'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    {session.session_name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Chat Area */}
          <div className="flex-1 flex flex-col">
            {currentSession ? (
              <>
                <div className="flex-1 overflow-y-auto p-6">
                  {messages.length === 0 ? (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-gray-500">No messages yet. Start typing!</p>
                    </div>
                  ) : (
                    <div>
                      {messages.map((msg, i) => (
                        <ChatMessage key={i} message={msg} />
                      ))}
                    </div>
                  )}
                </div>

                <form onSubmit={handleSendMessage} className="border-t border-gray-200 p-4">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Ask a question..."
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      type="submit"
                      disabled={loading}
                      className="btn btn-primary"
                    >
                      {loading ? 'Sending...' : 'Send'}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="flex items-center justify-center h-full">
                <button
                  onClick={handleNewSession}
                  className="btn btn-primary text-lg"
                >
                  Start a New Chat
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
