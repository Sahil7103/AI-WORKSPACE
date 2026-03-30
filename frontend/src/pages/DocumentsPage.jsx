import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import DocumentCard from '../components/DocumentCard'
import { authAPI, documentsAPI } from '../services/api'

const DocumentsPage = () => {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

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
    const fetchDocuments = async () => {
      try {
        const response = await documentsAPI.list()
        setDocuments(response.data.documents)
      } catch (error) {
        toast.error('Failed to load documents')
      }
    }
    fetchDocuments()
  }, [])

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await documentsAPI.upload(formData)
      setDocuments([...documents, response.data])
      setUploadProgress(0)
      toast.success('Document uploaded successfully!')
    } catch (error) {
      toast.error('Failed to upload document')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure?')) return

    try {
      await documentsAPI.delete(docId)
      setDocuments(documents.filter(d => d.id !== docId))
      toast.success('Document deleted!')
    } catch (error) {
      toast.error('Failed to delete document')
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
          <h1 className="text-3xl font-bold mb-8">Documents</h1>

          {/* Upload Section */}
          <div className="card mb-8">
            <h2 className="text-xl font-semibold mb-4">Upload Document</h2>
            <label className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition">
              <input
                type="file"
                onChange={handleFileUpload}
                disabled={loading}
                className="hidden"
                accept=".pdf,.docx,.txt"
              />
              <div>
                <p className="text-gray-600 mb-2">📤 Click to upload or drag and drop</p>
                <p className="text-sm text-gray-500">PDF, DOCX, TXT (max 50MB)</p>
                {loading && <p className="text-blue-600 mt-2">Uploading... {uploadProgress}%</p>}
              </div>
            </label>
          </div>

          {/* Documents Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {documents.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No documents yet. Upload one to get started!</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default DocumentsPage
