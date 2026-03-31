import React from 'react'
import { formatDate } from '../utils/helpers'

const ChatMessage = ({ message }) => {
  const isAssistant = message.role === 'assistant'

  return (
    <div
      className={`chat-message ${
        isAssistant ? 'chat-message--assistant' : 'chat-message--user'
      }`.trim()}
    >
      <div className="chat-message__avatar">{isAssistant ? 'AI' : 'ME'}</div>

      <div className="chat-message__body">
        <div className="chat-message__meta">
          <span className="chat-message__role">
            {isAssistant ? 'Copilot' : 'You'}
          </span>
          <span className="chat-message__time">{formatDate(message.created_at)}</span>
        </div>

        <div className="chat-message__bubble">
          <p className="chat-message__content">{message.content}</p>

          {message.sources && message.sources.length > 0 ? (
            <details className="chat-message__sources">
              <summary>Sources</summary>
              <ul className="chat-message__source-list">
                {message.sources.map((src, i) => (
                  <li key={i}>{src.filename || src.title || `Source ${i + 1}`}</li>
                ))}
              </ul>
            </details>
          ) : null}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
