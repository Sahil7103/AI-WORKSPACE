import React, { useEffect, useState } from 'react'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import { authAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'

const DashboardPage = () => {
  const [user, setUser] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await authAPI.getMe()
        setUser(response.data)
      } catch (error) {
        navigate('/login')
      }
    }
    fetchUser()
  }, [navigate])

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
        
        <main className="flex-1 overflow-auto p-8">
          <h1 className="text-3xl font-bold mb-8">Welcome, {user.full_name || user.username}!</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">💬 Start Chatting</h3>
              <p className="text-gray-600 mb-4">
                Upload documents and ask questions about them.
              </p>
              <button
                onClick={() => navigate('/chat')}
                className="btn btn-primary w-full"
              >
                Go to Chat
              </button>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold mb-4">📄 Manage Documents</h3>
              <p className="text-gray-600 mb-4">
                Upload, view, and manage your documents.
              </p>
              <button
                onClick={() => navigate('/documents')}
                className="btn btn-primary w-full"
              >
                Go to Documents
              </button>
            </div>

            {user.role === 'admin' && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">⚙️ Administration</h3>
                <p className="text-gray-600 mb-4">
                  Manage users and system settings.
                </p>
                <button
                  onClick={() => navigate('/admin')}
                  className="btn btn-primary w-full"
                >
                  Go to Admin
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default DashboardPage
