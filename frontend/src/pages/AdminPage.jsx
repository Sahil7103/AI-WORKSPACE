import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppShell from '../components/AppShell'
import { authAPI, adminAPI } from '../services/api'
import { ShieldAlert, Users, Trash2, HardDrive, Cpu, Activity, Zap } from 'lucide-react'

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
        prev.map((entry) => (entry.id === userId ? { ...entry, role: newRole } : entry))
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

  if (!user) return <div className="flex h-screen items-center justify-center text-[#A1A1AA]">Secure auth...</div>

  return (
    <AppShell user={user} onLogout={handleLogout}>
      <div className="max-w-7xl mx-auto px-6 py-10 w-full space-y-12">
        
        {/* Header Block Minimal */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[#3F3F46]">
          <div>
            <h1 className="text-3xl font-serif text-[#F4F4F5] tracking-tight flex items-center gap-3">
              <ShieldAlert className="text-[#EA580C]" size={32} />
              Admin
            </h1>
            <p className="text-[#A1A1AA] mt-2">Manage workspace users and analytics.</p>
          </div>
          <button 
            onClick={handleClearCache} 
            disabled={loading} 
            className="inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold border border-[#EF4444] text-[#EF4444] hover:bg-[#EF4444]/10 transition-colors disabled:opacity-50"
          >
            <Trash2 size={18} />
            <span>{loading ? 'Clearing cache...' : 'Clear cache'}</span>
          </button>
        </div>

        {/* System Stats Block */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-[#27272A] border border-[#3F3F46] p-6 rounded-3xl flex flex-col items-center justify-center gap-2">
              <HardDrive size={24} className="text-[#A1A1AA] mb-2" />
              <p className="text-3xl font-bold text-[#F4F4F5]">{stats.total_documents}</p>
              <span className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">Documents</span>
            </div>
            <div className="bg-[#27272A] border border-[#3F3F46] p-6 rounded-3xl flex flex-col items-center justify-center gap-2">
              <Cpu size={24} className="text-[#10A37F] mb-2" />
              <p className="text-3xl font-bold text-[#F4F4F5]">{stats.total_processed}</p>
              <span className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">Processed</span>
            </div>
            <div className="bg-[#27272A] border border-[#3F3F46] p-6 rounded-3xl flex flex-col items-center justify-center gap-2">
              <Zap size={24} className="text-[#3B82F6] mb-2" />
              <p className="text-3xl font-bold text-[#F4F4F5]">{stats.total_with_embeddings}</p>
              <span className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">Embedded</span>
            </div>
            <div className="bg-[#27272A] border border-[#3F3F46] p-6 rounded-3xl flex flex-col items-center justify-center gap-2">
              <Activity size={24} className="text-[#EA580C] mb-2" />
              <p className="text-3xl font-bold text-[#F4F4F5]">{stats.total_chunks}</p>
              <span className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">Chunks</span>
            </div>
          </div>
        )}

        {/* User Management */}
        <div className="bg-[#27272A] border border-[#3F3F46] rounded-3xl overflow-hidden shadow-lg">
          <div className="p-6 border-b border-[#3F3F46] flex items-center gap-3">
             <Users size={20} className="text-[#A1A1AA]" />
             <h2 className="text-lg font-semibold text-[#F4F4F5]">Team Management</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-[#F4F4F5]">
              <thead className="bg-[#18181A] text-xs uppercase font-medium text-[#A1A1AA]">
                <tr>
                  <th className="px-6 py-4">Username</th>
                  <th className="px-6 py-4">Email</th>
                  <th className="px-6 py-4">Role</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#3F3F46]">
                {users.map((entry) => (
                  <tr key={entry.id} className="hover:bg-[#3F3F46]/30 transition-colors">
                    <td className="px-6 py-4 font-medium">{entry.username}</td>
                    <td className="px-6 py-4 text-[#A1A1AA]">{entry.email}</td>
                    <td className="px-6 py-4 capitalize">{entry.role}</td>
                    <td className="px-6 py-4">
                      {entry.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-[#10A37F]/10 text-[#10A37F] border border-[#10A37F]/20">Active</span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/20">Inactive</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {entry.role !== 'admin' && (
                        <button onClick={() => handleUpdateRole(entry.id, 'admin')} className="text-xs text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#3F3F46] px-3 py-1.5 rounded-lg transition-colors border border-[#3F3F46] bg-[#18181A]">
                          Make admin
                        </button>
                      )}
                      {entry.role !== 'employee' && (
                        <button onClick={() => handleUpdateRole(entry.id, 'employee')} className="text-xs text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#3F3F46] px-3 py-1.5 rounded-lg transition-colors border border-[#3F3F46] bg-[#18181A]">
                          Make employee
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </AppShell>
  )
}

export default AdminPage
