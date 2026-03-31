import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppShell from '../components/AppShell'
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
      } catch {
        toast.error('Failed to load documents')
      }
    }

    fetchDocuments()
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
          setUploadProgress(
            Math.round((progressEvent.loaded * 100) / progressEvent.total)
          )
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

  if (!user) return <div className="page-loading">Loading documents...</div>

  return (
    <AppShell
      user={user}
      onLogout={handleLogout}
      title="Documents"
      subtitle="Organize your knowledge base in a cleaner, more professional workspace."
      actions={
        <label className="btn btn-primary cursor-pointer">
          Upload file
          <input
            type="file"
            onChange={handleFileUpload}
            disabled={loading}
            className="hidden"
            accept=".pdf,.docx,.txt"
          />
        </label>
      }
    >
      <div className="page-stack">
        <section className="documents-summary">
          <article className="stat-card">
            <span className="stat-card__label">Files</span>
            <strong className="stat-card__value">{documents.length}</strong>
            <p className="stat-card__hint">Available in your workspace</p>
          </article>
          <article className="stat-card">
            <span className="stat-card__label">Processed</span>
            <strong className="stat-card__value">
              {documents.filter((doc) => doc.is_processed).length}
            </strong>
            <p className="stat-card__hint">Ready for retrieval</p>
          </article>
          <article className="stat-card">
            <span className="stat-card__label">Embeddings</span>
            <strong className="stat-card__value">
              {documents.filter((doc) => doc.embedding_generated).length}
            </strong>
            <p className="stat-card__hint">Indexed for AI responses</p>
          </article>
        </section>

        <section className="documents-layout">
          <section className="surface-card surface-card--tall">
            <div className="surface-card__header">
              <div>
                <p className="surface-card__eyebrow">Upload</p>
                <h2 className="surface-card__title">Add a new document</h2>
              </div>
            </div>

            <label className="upload-dropzone">
              <input
                type="file"
                onChange={handleFileUpload}
                disabled={loading}
                className="hidden"
                accept=".pdf,.docx,.txt"
              />
              <p className="upload-dropzone__title">Drop a file here or click to browse</p>
              <p className="upload-dropzone__meta">
                PDF, DOCX, and TXT are supported up to 50MB.
              </p>
              {loading ? (
                <div className="upload-progress">
                  <div className="upload-progress__bar">
                    <span
                      className="upload-progress__fill"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="upload-dropzone__status">
                    Uploading... {uploadProgress}%
                  </p>
                </div>
              ) : null}
            </label>
          </section>

          <aside className="surface-card surface-card--tall">
            <p className="surface-card__eyebrow">Workspace guidance</p>
            <h2 className="surface-card__title">Keep uploads clean and searchable</h2>
            <div className="info-list">
              <div className="info-list__item">
                <span className="info-list__label">Recommended</span>
                <p>Use text-based PDF, DOCX, or TXT files for the best retrieval results.</p>
              </div>
              <div className="info-list__item">
                <span className="info-list__label">Processing</span>
                <p>Files with extracted text are processed immediately after upload.</p>
              </div>
              <div className="info-list__item">
                <span className="info-list__label">Limit</span>
                <p>Maximum size is 50MB per file in the current setup.</p>
              </div>
            </div>
          </aside>
        </section>

        {documents.length === 0 ? (
          <section className="empty-state">
            <h3 className="empty-state__title">No documents yet</h3>
            <p className="empty-state__text">
              Upload your first file to start building a knowledge base for chat.
            </p>
          </section>
        ) : (
          <section className="documents-grid">
            {documents.map((doc) => (
              <DocumentCard key={doc.id} document={doc} onDelete={handleDelete} />
            ))}
          </section>
        )}
      </div>
    </AppShell>
  )
}

export default DocumentsPage
