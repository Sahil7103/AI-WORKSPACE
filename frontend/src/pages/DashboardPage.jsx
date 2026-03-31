import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/AppShell'
import { authAPI } from '../services/api'

const DashboardPage = () => {
  const [user, setUser] = useState(null)
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

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  if (!user) return <div className="page-loading">Loading workspace...</div>

  return (
    <AppShell
      user={user}
      onLogout={handleLogout}
      title={`Welcome back, ${user.full_name || user.username}`}
      subtitle="A ChatGPT-style workspace for conversations, documents, and team operations."
      actions={
        <button onClick={() => navigate('/chat')} className="btn btn-primary">
          Open chat
        </button>
      }
    >
      <div className="page-stack">
        <section className="hero-panel">
          <div>
            <p className="hero-panel__eyebrow">Ready to work</p>
            <h2 className="hero-panel__title">
              Ask questions, manage files, and stay in one clean workflow.
            </h2>
            <p className="hero-panel__text">
              This pass is frontend-only. The backend APIs and data flow stay exactly where they were.
            </p>
          </div>

          <div className="hero-panel__actions">
            <button onClick={() => navigate('/chat')} className="btn btn-primary">
              Start a conversation
            </button>
            <button onClick={() => navigate('/documents')} className="btn btn-secondary">
              Review documents
            </button>
          </div>
        </section>

        <section className="dashboard-grid">
          <article className="surface-card surface-card--tall">
            <p className="surface-card__eyebrow">Chat</p>
            <h3 className="surface-card__title">Start a new thread</h3>
            <p className="surface-card__text">
              Jump into a focused chat interface with recent sessions in the sidebar and a bottom composer.
            </p>
            <button onClick={() => navigate('/chat')} className="btn btn-secondary">
              Go to chat
            </button>
          </article>

          <article className="surface-card surface-card--tall">
            <p className="surface-card__eyebrow">Documents</p>
            <h3 className="surface-card__title">Upload and organize knowledge</h3>
            <p className="surface-card__text">
              Keep PDFs, DOCX files, and text documents ready for retrieval while preserving the current backend.
            </p>
            <button onClick={() => navigate('/documents')} className="btn btn-secondary">
              Open documents
            </button>
          </article>

          <article className="surface-card surface-card--tall">
            <p className="surface-card__eyebrow">Account</p>
            <h3 className="surface-card__title">{user.email}</h3>
            <p className="surface-card__text">
              Signed in as <strong>{user.role}</strong>. Permissions are unchanged in this redesign.
            </p>
            {user.role === 'admin' ? (
              <button onClick={() => navigate('/admin')} className="btn btn-secondary">
                Open admin tools
              </button>
            ) : (
              <button onClick={handleLogout} className="btn btn-secondary">
                Log out
              </button>
            )}
          </article>
        </section>
      </div>
    </AppShell>
  )
}

export default DashboardPage
