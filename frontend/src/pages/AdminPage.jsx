import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import { authAPI, adminAPI } from '../services/api'

const AdminPage = () => {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await authAPI.getMe()
        setUser(response.data)
        if (response.data.role !== 'admin') {
          navigate('/')
        }
      } catch {
        navigate('/login')
      }
    }
    fetchUser()
  }, [navigate])

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        const [usersRes, statsRes] = await Promise.all([
          adminAPI.listUsers(),
          adminAPI.getStats(),
        ])
        setUsers(usersRes.data.users)
        setStats(statsRes.data)
      } catch (error) {
        toast.error('Failed to load admin data')
      }
    }
    if (user?.role === 'admin') {
      fetchAdminData()
    }
  }, [user])

  const handleUpdateRole = async (userId, newRole) => {
    try {
      await adminAPI.updateUserRole(userId, newRole)
      setUsers(users.map(u => u.id === userId ? { ...u, role: newRole } : u))
      toast.success('User role updated!')
    } catch (error) {
      toast.error('Failed to update user role')
    }
  }

  const handleClearCache = async () => {
    try {
      setLoading(true)
      await adminAPI.clearCache()
      toast.success('Cache cleared!')
    } catch (error) {
      toast.error('Failed to clear cache')
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

        <main className="flex-1 overflow-auto p-8">
          <h1 className="text-3xl font-bold mb-8">Administration</h1>

          {/* Statistics */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="card text-center">
                <p className="text-3xl font-bold text-blue-600">{stats.total_documents}</p>
                <p className="text-gray-600">Total Documents</p>
              </div>
              <div className="card text-center">
                <p className="text-3xl font-bold text-green-600">{stats.total_processed}</p>
                <p className="text-gray-600">Processed</p>
              </div>
              <div className="card text-center">
                <p className="text-3xl font-bold text-purple-600">{stats.total_with_embeddings}</p>
                <p className="text-gray-600">Embedded</p>
              </div>
              <div className="card text-center">
                <p className="text-3xl font-bold text-orange-600">{stats.total_chunks}</p>
                <p className="text-gray-600">Chunks</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="card mb-8">
            <h2 className="text-xl font-semibold mb-4">System Actions</h2>
            <button
              onClick={handleClearCache}
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? 'Clearing...' : 'Clear Cache'}
            </button>
          </div>

          {/* Users Table */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">User Management</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-4">Username</th>
                    <th className="text-left py-2 px-4">Email</th>
                    <th className="text-left py-2 px-4">Role</th>
                    <th className="text-left py-2 px-4">Status</th>
                    <th className="text-left py-2 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b hover:bg-gray-50">
                      <td className="py-2 px-4">{u.username}</td>
                      <td className="py-2 px-4">{u.email}</td>
                      <td className="py-2 px-4">{u.role}</td>
                      <td className="py-2 px-4">
                        <span className={u.is_active ? 'text-green-600' : 'text-red-600'}>
                          {u.is_active ? '✓ Active' : '✗ Inactive'}
                        </span>
                      </td>
                      <td className="py-2 px-4 space-x-2">
                        {u.role !== 'admin' && (
                          <button
                            onClick={() => handleUpdateRole(u.id, 'admin')}
                            className="btn btn-secondary text-sm"
                          >
                            Make Admin
                          </button>
                        )}
                        {u.role !== 'employee' && (
                          <button
                            onClick={() => handleUpdateRole(u.id, 'employee')}
                            className="btn btn-secondary text-sm"
                          >
                            Make Employee
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default AdminPage
