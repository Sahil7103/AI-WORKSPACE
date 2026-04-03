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
    <div className="flex min-h-screen items-center justify-center bg-[#18181A] text-[#F4F4F5] px-4">
      <div className="w-full max-w-md bg-[#27272A] p-8 rounded-3xl border border-[#3F3F46] shadow-2xl">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4 text-[#EA580C]">
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-12 h-12">
              <path d="M12 2L13.5 10.5L22 12L13.5 13.5L12 22L10.5 13.5L2 12L10.5 10.5L12 2Z" />
            </svg>
          </div>
          <h1 className="text-3xl font-serif tracking-tight">Welcome back</h1>
          <p className="text-[#A1A1AA] mt-2 text-sm">Log in to continue to your workspace</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-[#A1A1AA]">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-[#18181A] border border-[#3F3F46] rounded-xl px-4 py-3 text-[#F4F4F5] focus:outline-none focus:border-[#EA580C] focus:ring-1 focus:ring-[#EA580C] transition-colors"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-[#A1A1AA]">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[#18181A] border border-[#3F3F46] rounded-xl px-4 py-3 text-[#F4F4F5] focus:outline-none focus:border-[#EA580C] focus:ring-1 focus:ring-[#EA580C] transition-colors"
              required
            />
          </div>

          <button 
            type="submit" 
            disabled={loading} 
            className="w-full py-3 mt-4 bg-[#EA580C] text-white rounded-xl font-medium hover:bg-[#C2410C] transition-colors disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Continue'}
          </button>
        </form>

        <p className="text-center mt-6 text-sm text-[#A1A1AA]">
          Don't have an account?{' '}
          <Link to="/register" className="text-[#EA580C] hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
