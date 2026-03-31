import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authAPI } from '../services/api'

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
  })
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      await authAPI.register(formData)
      toast.success('Registration successful. Please log in.')
      navigate('/login')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-page__backdrop" />

      <div className="auth-page__content">
        <section className="auth-page__intro">
          <p className="auth-page__eyebrow">Create your workspace access</p>
          <h1 className="auth-page__title">
            Join the same ChatGPT-style UI with your current backend underneath.
          </h1>
          <p className="auth-page__text">
            Registration still uses the existing API. This pass only changes the frontend experience and visual system.
          </p>

          <div className="auth-page__feature-list">
            <div className="auth-page__feature">
              <span className="auth-page__feature-kicker">Simple onboarding</span>
              <p>Create your account in one step and move straight into the workspace.</p>
            </div>
            <div className="auth-page__feature">
              <span className="auth-page__feature-kicker">Professional flow</span>
              <p>Cleaner structure, stronger hierarchy, and easier-to-scan forms.</p>
            </div>
            <div className="auth-page__feature">
              <span className="auth-page__feature-kicker">Backend preserved</span>
              <p>Roles, auth, document APIs, and data handling remain unchanged.</p>
            </div>
          </div>

          <div className="auth-page__metric-row">
            <div className="auth-page__metric">
              <strong>Workspace</strong>
              <span>Chat, docs, and admin in one shell</span>
            </div>
            <div className="auth-page__metric">
              <strong>Access</strong>
              <span>Uses your existing registration API</span>
            </div>
          </div>
        </section>

        <section className="auth-card">
          <div className="auth-card__header">
            <p className="auth-card__eyebrow">New account</p>
            <h2 className="auth-card__title">Register</h2>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="field">
              <label className="field__label">Full name</label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                className="field__input"
                required
              />
            </div>

            <div className="field">
              <label className="field__label">Username</label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className="field__input"
                required
              />
            </div>

            <div className="field">
              <label className="field__label">Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="field__input"
                required
              />
            </div>

            <div className="field">
              <label className="field__label">Password</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="field__input"
                required
              />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary btn-block">
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="auth-card__footer">
            Already have an account?{' '}
            <Link to="/login" className="auth-card__link">
              Log in
            </Link>
          </p>
        </section>
      </div>
    </div>
  )
}

export default RegisterPage
