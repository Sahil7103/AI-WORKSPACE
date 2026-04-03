import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authAPI } from '../services/api'

const RegisterPage = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      await authAPI.register({
        username,
        password,
        email,
        full_name: fullName,
      })
      toast.success('Registration successful! Please log in.')
      navigate('/login')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#18181A] text-[#F4F4F5] px-4 py-8">
      <div className="w-full max-w-md bg-[#27272A] p-8 rounded-3xl border border-[#3F3F46] shadow-2xl">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4 text-[#EA580C]">
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-12 h-12">
              <path d="M12 2L13.5 10.5L22 12L13.5 13.5L12 22L10.5 13.5L2 12L10.5 10.5L12 2Z" />
            </svg>
          </div>
          <h1 className="text-3xl font-serif tracking-tight">Create account</h1>
          <p className="text-[#A1A1AA] mt-2 text-sm">Join to access the workspace</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-[#A1A1AA]">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full bg-[#18181A] border border-[#3F3F46] rounded-xl px-4 py-3 text-[#F4F4F5] focus:outline-none focus:border-[#EA580C] focus:ring-1 focus:ring-[#EA580C] transition-colors"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-[#A1A1AA]">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[#18181A] border border-[#3F3F46] rounded-xl px-4 py-3 text-[#F4F4F5] focus:outline-none focus:border-[#EA580C] focus:ring-1 focus:ring-[#EA580C] transition-colors"
              required
            />
          </div>

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
              minLength={6}
            />
          </div>

          <button 
            type="submit" 
            disabled={loading} 
            className="w-full py-3 mt-4 bg-[#EA580C] text-white rounded-xl font-medium hover:bg-[#C2410C] transition-colors disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Sign up'}
          </button>
        </form>

        <p className="text-center mt-6 text-sm text-[#A1A1AA]">
          Already have an account?{' '}
          <Link to="/login" className="text-[#EA580C] hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
