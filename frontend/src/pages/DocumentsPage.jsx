import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppShell from '../components/AppShell'
import DocumentCard from '../components/DocumentCard'
import { authAPI, documentsAPI } from '../services/api'
import { UploadCloud, FileText, Database, Terminal } from 'lucide-react'

const DocumentsPage = () => {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.list()
      setDocuments(response.data.documents)
    } catch {
      toast.error('Failed to load documents')
    }
  }

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
    loadDocuments()
  }, [])

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await documentsAPI.upload(formData, {
        onUploadProgress: (progressEvent) => {
          if (!progressEvent.total) return
          setUploadProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total))
        },
      })
      setDocuments((prev) => [...prev, response.data])
      setUploadProgress(0)
      toast.success('Document uploaded successfully')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload document')
    } finally {
      setLoading(false)
      e.target.value = ''
    }
  }

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure?')) return

    try {
      await documentsAPI.delete(docId)
      setDocuments((prev) => prev.filter((doc) => doc.id !== docId))
      toast.success('Document deleted')
    } catch {
      toast.error('Failed to delete document')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  if (!user) return <div className="flex h-screen items-center justify-center text-[#A1A1AA]">Loading documents...</div>

  return (
    <AppShell user={user} onLogout={handleLogout}>
      <div className="max-w-7xl mx-auto px-6 py-10 w-full space-y-12">
        
        {/* Header Block Minimal */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[#3F3F46]">
          <div>
            <h1 className="text-3xl font-serif text-[#F4F4F5] tracking-tight">Documents</h1>
            <p className="text-[#A1A1AA] mt-2">Upload and manage knowledge bases for Sarthi.</p>
          </div>
          <label className="inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold bg-[#F4F4F5] text-[#18181A] hover:bg-[#D4D4D8] transition-colors cursor-pointer">
            <UploadCloud size={18} />
            <span>Upload file</span>
            <input type="file" onChange={handleFileUpload} disabled={loading} className="hidden" accept=".pdf,.docx,.txt" />
          </label>
        </div>

        {/* Upload Zone & Stats Matrix */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Dropzone */}
          <div className="lg:col-span-2">
            <label className={`flex flex-col items-center justify-center gap-4 rounded-3xl border-2 border-dashed ${loading ? 'border-[#EA580C]/50 bg-[#EA580C]/5' : 'border-[#3F3F46] hover:border-[#EA580C] bg-[#27272A]/50 hover:bg-[#27272A]'} p-12 text-center transition-all cursor-pointer h-full min-h-[250px]`}>
              <input type="file" onChange={handleFileUpload} disabled={loading} className="hidden" accept=".pdf,.docx,.txt" />
              {loading ? (
                <div className="w-full max-w-sm">
                  <div className="h-2 w-full bg-[#18181A] rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-[#EA580C] transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                  </div>
                  <p className="text-sm text-[#F4F4F5]">Uploading... {uploadProgress}%</p>
                </div>
              ) : (
                <>
                  <UploadCloud size={40} className="text-[#A1A1AA]" />
                  <div>
                    <p className="text-lg font-medium text-[#F4F4F5]">Drag & drop or browse</p>
                    <p className="text-sm text-[#A1A1AA] mt-1">PDF, DOCX, TXT up to 50MB.</p>
                  </div>
                </>
              )}
            </label>
          </div>

          {/* Quick Stats side panel */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between p-5 rounded-2xl bg-[#27272A] border border-[#3F3F46]">
              <div>
                <span className="text-xs uppercase tracking-wider font-semibold text-[#A1A1AA]">Total Files</span>
                <p className="text-2xl font-bold text-[#F4F4F5] mt-1">{documents.length}</p>
              </div>
              <FileText size={24} className="text-[#3F3F46]" />
            </div>
            <div className="flex items-center justify-between p-5 rounded-2xl bg-[#27272A] border border-[#3F3F46]">
              <div>
                <span className="text-xs uppercase tracking-wider font-semibold text-[#A1A1AA]">Processed</span>
                <p className="text-2xl font-bold text-[#F4F4F5] mt-1">{documents.filter((doc) => doc.is_processed).length}</p>
              </div>
              <Terminal size={24} className="text-[#3F3F46]" />
            </div>
            <div className="flex items-center justify-between p-5 rounded-2xl bg-[#27272A] border border-[#3F3F46]">
              <div>
                <span className="text-xs uppercase tracking-wider font-semibold text-[#A1A1AA]">Embedded</span>
                <p className="text-2xl font-bold text-[#F4F4F5] mt-1">{documents.filter((doc) => doc.embedding_generated).length}</p>
              </div>
              <Database size={24} className="text-[#3F3F46]" />
            </div>
          </div>
        </div>

        {/* Documents Grid */}
        <div>
          <h2 className="text-xl font-serif text-[#F4F4F5] mb-6">Your Database</h2>
          {documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-16 text-center border border-[#3F3F46] rounded-3xl bg-[#27272A]/30 border-dashed">
              <h3 className="text-lg font-medium text-[#F4F4F5]">No documents built</h3>
              <p className="text-[#A1A1AA] mt-2 max-w-sm">Upload your first data source to ground Sarthi in your custom knowledge.</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {documents.map((doc) => (
                <DocumentCard key={doc.id} document={doc} onDelete={handleDelete} />
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}

export default DocumentsPage
