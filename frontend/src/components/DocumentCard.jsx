import React from 'react'
import { formatDate, formatFileSize } from '../utils/helpers'

const DocumentCard = ({ document, onDelete }) => {
  return (
    <article className="flex justify-between items-start bg-[#27272A] border border-[#3F3F46] rounded-2xl p-5 hover:border-[#F4F4F5]/30 transition-colors shadow-lg group">
      <div className="flex-1 min-w-0 pr-4">
        <p className="text-xs font-semibold text-[#EA580C] uppercase tracking-wider mb-2">Knowledge file</p>
        <h3 className="text-lg font-bold text-[#F4F4F5] break-all truncate">{document.filename}</h3>
        
        <div className="flex flex-wrap gap-2 mt-4">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-[#1E1E1E] text-[#F4F4F5] border border-[#3F3F46]">
            {document.file_type.toUpperCase()}
          </span>
          {document.is_processed && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-[#10A37F]/10 text-[#10A37F] border border-[#10A37F]/20">
              Processed
            </span>
          )}
          {document.embedding_generated && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20">
              Embedded
            </span>
          )}
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t border-[#3F3F46]">
          <div>
            <span className="block text-xs text-[#A1A1AA] mb-1">Size</span>
            <p className="text-sm text-[#F4F4F5] font-medium">{formatFileSize(document.size_bytes)}</p>
          </div>
          <div>
            <span className="block text-xs text-[#A1A1AA] mb-1">Embedding</span>
            <p className="text-sm text-[#F4F4F5] font-medium">{document.embedding_generated ? 'Ready' : 'Pending'}</p>
          </div>
          <div>
            <span className="block text-xs text-[#A1A1AA] mb-1">Created</span>
            <p className="text-sm text-[#F4F4F5] font-medium truncate">{formatDate(document.created_at)}</p>
          </div>
        </div>
      </div>

      <button 
        onClick={() => onDelete(document.id)} 
        className="shrink-0 p-2 text-[#A1A1AA] hover:text-[#EF4444] hover:bg-[#EF4444]/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 6h18"></path>
          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
          <line x1="10" y1="11" x2="10" y2="17"></line>
          <line x1="14" y1="11" x2="14" y2="17"></line>
        </svg>
      </button>
    </article>
  )
}

export default DocumentCard
