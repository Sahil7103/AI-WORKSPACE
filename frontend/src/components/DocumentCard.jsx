import React from 'react'

const DocumentCard = ({ document, onDelete }) => {
  const getFileTypeColor = (type) => {
    const colors = {
      pdf: 'bg-red-100 text-red-800',
      docx: 'bg-blue-100 text-blue-800',
      txt: 'bg-gray-100 text-gray-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="card">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{document.filename}</h3>
          <div className="flex items-center space-x-2 mt-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getFileTypeColor(document.file_type)}`}>
              {document.file_type.toUpperCase()}
            </span>
            {document.is_processed && (
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ✓ Processed
              </span>
            )}
          </div>
        </div>
        <button
          onClick={() => onDelete(document.id)}
          className="btn btn-danger text-sm"
        >
          Delete
        </button>
      </div>
      
      <div className="text-sm text-gray-600 space-y-1">
        <p>Size: {(document.size_bytes / 1024).toFixed(2)} KB</p>
        <p>Status: {document.embedding_generated ? 'Embedded' : 'Pending'}</p>
      </div>
    </div>
  )
}

export default DocumentCard
