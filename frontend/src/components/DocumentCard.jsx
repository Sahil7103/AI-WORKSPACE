import React from 'react'
import { formatDate, formatFileSize } from '../utils/helpers'

const DocumentCard = ({ document, onDelete }) => {
  const getFileTypeColor = (type) => {
    const colors = {
      pdf: 'status-pill status-pill--pdf',
      docx: 'status-pill status-pill--docx',
      txt: 'status-pill status-pill--txt',
    }
    return colors[type] || 'status-pill'
  }

  return (
    <article className="document-card">
      <div className="document-card__top">
        <div className="document-card__copy">
          <p className="document-card__eyebrow">Knowledge file</p>
          <h3 className="document-card__title">{document.filename}</h3>
          <div className="document-card__pills">
            <span className={getFileTypeColor(document.file_type)}>
              {document.file_type.toUpperCase()}
            </span>
            {document.is_processed ? (
              <span className="status-pill status-pill--success">Processed</span>
            ) : null}
            {document.embedding_generated ? (
              <span className="status-pill status-pill--neutral">Embedded</span>
            ) : null}
          </div>
        </div>

        <button onClick={() => onDelete(document.id)} className="btn btn-ghost-danger">
          Delete
        </button>
      </div>

      <div className="document-card__details">
        <div>
          <span className="document-card__label">Size</span>
          <p>{formatFileSize(document.size_bytes)}</p>
        </div>
        <div>
          <span className="document-card__label">Embedding</span>
          <p>{document.embedding_generated ? 'Ready' : 'Pending'}</p>
        </div>
        <div>
          <span className="document-card__label">Created</span>
          <p>{formatDate(document.created_at)}</p>
        </div>
      </div>
    </article>
  )
}

export default DocumentCard
