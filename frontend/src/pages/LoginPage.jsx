import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authAPI } from '../services/api'

const LoginPage = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await authAPI.login(username, password)
      localStorage.setItem('auth_token', response.data.access_token)
      toast.success('Logged in successfully')
      navigate('/')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-page__backdrop" />

      <div className="auth-page__content">
        <section className="auth-page__intro">
          <p className="auth-page__eyebrow">AI Workplace Copilot</p>
          <h1 className="auth-page__title">
            A familiar ChatGPT-style workspace for your internal knowledge.
          </h1>
          <p className="auth-page__text">
            Sign in to chat with your documents, manage uploads, and work inside the refreshed interface.
          </p>

          <div className="auth-page__feature-list">
            <div className="auth-page__feature">
              <span className="auth-page__feature-kicker">Focused</span>
              <p>One clean workspace for chat, knowledge files, and team operations.</p>
            </div>
            <div className="auth-page__feature">
              <span className="auth-page__feature-kicker">Fast</span>
              <p>Recent threads, uploads, and answers stay in one predictable flow.</p>
            </div>
            <div className="auth-page__feature">
              <span className="auth-page__feature-kicker">Safe</span>
              <p>Your current backend and auth model stay exactly as they are.</p>
            </div>
          </div>

          <div className="auth-page__metric-row">
            <div className="auth-page__metric">
              <strong>Chat</strong>
              <span>Document-grounded conversations</span>
            </div>
            <div className="auth-page__metric">
              <strong>Upload</strong>
              <span>PDF, DOCX, and TXT support</span>
            </div>
          </div>
        </section>

        <section className="auth-card">
          <div className="auth-card__header">
            <p className="auth-card__eyebrow">Welcome back</p>
            <h2 className="auth-card__title">Log in</h2>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="field">
              <label className="field__label">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="field__input"
                required
              />
            </div>

            <div className="field">
              <label className="field__label">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="field__input"
                required
              />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary btn-block">
              {loading ? 'Logging in...' : 'Continue'}
            </button>
          </form>

          <p className="auth-card__footer">
            Do not have an account?{' '}
            <Link to="/register" className="auth-card__link">
              Create one
            </Link>
          </p>
        </section>
      </div>
    </div>
  )
}

export default LoginPage
