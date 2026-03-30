import React, { useState } from 'react'
import { formatDate } from '../utils/helpers'

const ChatMessage = ({ message }) => {
  const isAssistant = message.role === 'assistant'

  return (
    <div className={`flex ${isAssistant ? 'justify-start' : 'justify-end'} mb-4`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isAssistant
            ? 'bg-gray-200 text-gray-900'
            : 'bg-blue-600 text-white'
        }`}
      >
        <p className="text-sm">{message.content}</p>
        {message.sources && message.sources.length > 0 && (
          <details className="mt-2 text-xs opacity-75">
            <summary className="cursor-pointer">Sources</summary>
            <ul className="mt-1 list-disc list-inside">
              {message.sources.map((src, i) => (
                <li key={i}>{src.filename}</li>
              ))}
            </ul>
          </details>
        )}
        <span className="text-xs opacity-70 mt-1">
          {formatDate(message.created_at)}
        </span>
      </div>
    </div>
  )
}

export default ChatMessage
