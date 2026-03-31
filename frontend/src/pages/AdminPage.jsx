import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppShell from '../components/AppShell'
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
      } catch {
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
      setUsers((prev) =>
        prev.map((entry) =>
          entry.id === userId ? { ...entry, role: newRole } : entry
        )
      )
      toast.success('User role updated')
    } catch {
      toast.error('Failed to update user role')
    }
  }

  const handleClearCache = async () => {
    try {
      setLoading(true)
      await adminAPI.clearCache()
      toast.success('Cache cleared')
    } catch {
      toast.error('Failed to clear cache')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  if (!user) return <div className="page-loading">Loading admin console...</div>

  return (
    <AppShell
      user={user}
      onLogout={handleLogout}
      title="Admin"
      subtitle="Manage system-wide usage without changing backend routes or permissions."
      actions={
        <button onClick={handleClearCache} disabled={loading} className="btn btn-primary">
          {loading ? 'Clearing cache...' : 'Clear cache'}
        </button>
      }
    >
      <div className="page-stack">
        {stats ? (
          <section className="admin-stats">
            <article className="stat-card">
              <span className="stat-card__label">Documents</span>
              <strong className="stat-card__value">{stats.total_documents}</strong>
              <p className="stat-card__hint">Stored files</p>
            </article>
            <article className="stat-card">
              <span className="stat-card__label">Processed</span>
              <strong className="stat-card__value">{stats.total_processed}</strong>
              <p className="stat-card__hint">Ready for search</p>
            </article>
            <article className="stat-card">
              <span className="stat-card__label">Embedded</span>
              <strong className="stat-card__value">{stats.total_with_embeddings}</strong>
              <p className="stat-card__hint">Vectorized content</p>
            </article>
            <article className="stat-card">
              <span className="stat-card__label">Chunks</span>
              <strong className="stat-card__value">{stats.total_chunks}</strong>
              <p className="stat-card__hint">Retrieval units</p>
            </article>
          </section>
        ) : null}

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">User management</p>
              <h2 className="surface-card__title">Access and roles</h2>
            </div>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.username}</td>
                    <td>{entry.email}</td>
                    <td className="capitalize">{entry.role}</td>
                    <td>
                      <span
                        className={`status-pill ${
                          entry.is_active ? 'status-pill--success' : 'status-pill--warning'
                        }`.trim()}
                      >
                        {entry.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="data-table__actions">
                      {entry.role !== 'admin' ? (
                        <button
                          onClick={() => handleUpdateRole(entry.id, 'admin')}
                          className="btn btn-secondary"
                        >
                          Make admin
                        </button>
                      ) : null}
                      {entry.role !== 'employee' ? (
                        <button
                          onClick={() => handleUpdateRole(entry.id, 'employee')}
                          className="btn btn-secondary"
                        >
                          Make employee
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </AppShell>
  )
}

export default AdminPage
