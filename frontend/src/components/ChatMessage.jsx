import React from 'react'
import { FileText, Sparkles } from 'lucide-react'
import { getInitials } from '../utils/helpers'

const formatSourceLabel = (source) => {
  if (!source || typeof source !== 'object') {
    return String(source || 'Source')
  }

  return source.filename || source.title || `Source ${source.doc_id || ''}`.trim()
}

const formatSimilarity = (source) => {
  if (!source || typeof source !== 'object' || typeof source.similarity !== 'number') {
    return null
  }

  return `${Math.round(source.similarity * 100)}% match`
}

const renderInline = (text) => {
  if (!text) return null

  const segments = text.split(/(`[^`]+`)/g)

  return segments.map((segment, index) => {
    if (!segment) return null

    if (segment.startsWith('`') && segment.endsWith('`')) {
      return (
        <code
          key={`code-${index}`}
          className="rounded-md bg-[#2A2A31] px-1.5 py-0.5 text-[0.95em] text-[#F5F5F5]"
        >
          {segment.slice(1, -1)}
        </code>
      )
    }

    const parts = []
    const regex = /(\*\*[^*]+\*\*|\*[^*]+\*)/g
    let lastIndex = 0
    let match

    while ((match = regex.exec(segment)) !== null) {
      if (match.index > lastIndex) {
        parts.push(segment.slice(lastIndex, match.index))
      }

      const token = match[0]
      if (token.startsWith('**')) {
        parts.push(
          <strong key={`strong-${index}-${match.index}`} className="font-semibold text-[#FAFAFA]">
            {token.slice(2, -2)}
          </strong>
        )
      } else {
        parts.push(
          <em key={`em-${index}-${match.index}`} className="italic text-[#F3F4F6]">
            {token.slice(1, -1)}
          </em>
        )
      }

      lastIndex = match.index + token.length
    }

    if (lastIndex < segment.length) {
      parts.push(segment.slice(lastIndex))
    }

    return <React.Fragment key={`text-${index}`}>{parts}</React.Fragment>
  })
}

const parseBlocks = (content) => {
  const lines = content.replace(/\r\n/g, '\n').split('\n')
  const blocks = []
  let paragraphLines = []
  let listBuffer = null

  const flushParagraph = () => {
    if (paragraphLines.length) {
      blocks.push({
        type: 'paragraph',
        text: paragraphLines.join(' '),
      })
      paragraphLines = []
    }
  }

  const flushList = () => {
    if (listBuffer?.items.length) {
      blocks.push(listBuffer)
    }
    listBuffer = null
  }

  lines.forEach((line) => {
    const trimmed = line.trim()

    if (!trimmed) {
      flushParagraph()
      flushList()
      return
    }

    const headingMatch = trimmed.match(/^(#{1,3})\s+(.*)$/)
    if (headingMatch) {
      flushParagraph()
      flushList()
      blocks.push({
        type: 'heading',
        level: headingMatch[1].length,
        text: headingMatch[2].trim(),
      })
      return
    }

    const bulletMatch = trimmed.match(/^[-*]\s+(.*)$/)
    if (bulletMatch) {
      flushParagraph()
      if (!listBuffer || listBuffer.type !== 'bullet') {
        flushList()
        listBuffer = { type: 'bullet', items: [] }
      }
      listBuffer.items.push(bulletMatch[1].trim())
      return
    }

    const numberedMatch = trimmed.match(/^\d+\.\s+(.*)$/)
    if (numberedMatch) {
      flushParagraph()
      if (!listBuffer || listBuffer.type !== 'numbered') {
        flushList()
        listBuffer = { type: 'numbered', items: [] }
      }
      listBuffer.items.push(numberedMatch[1].trim())
      return
    }

    if (listBuffer) {
      flushList()
    }

    paragraphLines.push(trimmed)
  })

  flushParagraph()
  flushList()

  return blocks
}

const renderBlocks = (content) => {
  const blocks = parseBlocks(content)

  return blocks.map((block, index) => {
    if (block.type === 'heading') {
      const headingClasses = {
        1: 'text-2xl font-semibold tracking-tight text-[#FAFAFA] mt-2',
        2: 'text-xl font-semibold tracking-tight text-[#FAFAFA] mt-2',
        3: 'text-lg font-semibold tracking-tight text-[#FAFAFA] mt-1',
      }

      const className = headingClasses[block.level] || headingClasses[3]
      if (block.level === 1) {
        return <h1 key={index} className={className}>{renderInline(block.text)}</h1>
      }
      if (block.level === 2) {
        return <h2 key={index} className={className}>{renderInline(block.text)}</h2>
      }
      return <h3 key={index} className={className}>{renderInline(block.text)}</h3>
    }

    if (block.type === 'bullet' || block.type === 'numbered') {
      const ListTag = block.type === 'numbered' ? 'ol' : 'ul'
      const listClassName =
        block.type === 'numbered'
          ? 'list-decimal space-y-3 pl-6 text-[17px] leading-8 text-[#E7E7EA] marker:text-[#A1A1AA]'
          : 'list-disc space-y-3 pl-6 text-[17px] leading-8 text-[#E7E7EA] marker:text-[#A1A1AA]'

      return (
        <ListTag key={index} className={listClassName}>
          {block.items.map((item, itemIndex) => (
            <li key={`${index}-${itemIndex}`}>{renderInline(item)}</li>
          ))}
        </ListTag>
      )
    }

    return (
      <p key={index} className="text-[17px] leading-8 text-[#E7E7EA]">
        {renderInline(block.text)}
      </p>
    )
  })
}

const ChatMessage = ({ message, user }) => {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-4 md:gap-5 px-2 md:px-3 py-2 md:py-3 ${isUser ? '' : ''}`}>
      <div className="flex-shrink-0 pt-1">
        {isUser ? (
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#3F3F46] text-xs font-semibold text-[#F4F4F5] shadow-sm">
            {getInitials(user?.full_name || user?.username || 'U').slice(0, 2)}
          </div>
        ) : (
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#2C1A11] text-[#F97316] shadow-sm shadow-[#EA580C]/10">
            <Sparkles size={17} strokeWidth={2.25} />
          </div>
        )}
      </div>

      <div className="min-w-0 flex-1">
        <div className="mb-3 flex items-center gap-2">
          <div className="text-sm font-semibold tracking-tight text-[#FAFAFA]">
            {isUser ? 'You' : 'Copilot'}
          </div>
          {!isUser ? (
            <span className="rounded-full border border-[#3F3F46] bg-[#232326] px-2 py-0.5 text-[11px] font-medium uppercase tracking-[0.12em] text-[#A1A1AA]">
              Assistant
            </span>
          ) : null}
        </div>

        <div
          className={`rounded-[1.6rem] border px-5 py-4 md:px-6 md:py-5 ${
            isUser
              ? 'border-[#3F3F46] bg-[#232326] text-[#F4F4F5]'
              : 'border-[#31271E] bg-[#1D1D21] shadow-[0_12px_30px_rgba(0,0,0,0.18)]'
          }`}
        >
          <div className="space-y-4">
            {isUser ? (
              <p className="text-[17px] leading-8 text-[#F4F4F5] whitespace-pre-wrap">
                {message.content}
              </p>
            ) : message.streaming ? (
              <div className="space-y-4">
                {message.content ? renderBlocks(message.content) : (
                  <p className="text-[17px] leading-8 text-[#E7E7EA]">Thinking…</p>
                )}
                <span className="inline-block h-5 w-[2px] animate-pulse rounded-full bg-[#F97316]" />
              </div>
            ) : (
              renderBlocks(message.content)
            )}
          </div>

          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-6 border-t border-[#31313A] pt-4">
              <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[#8F9098]">
                Sources
              </div>
              <div className="grid gap-2">
                {message.sources.map((source, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 rounded-2xl border border-[#353542] bg-[#24242A] px-3 py-3"
                  >
                    <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-[#2D2D36] text-[#B8BBC5]">
                      <FileText size={15} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-[#F4F4F5]">
                        {formatSourceLabel(source)}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-2 text-xs text-[#A1A1AA]">
                        {typeof source === 'object' && source.chunk_index !== undefined ? (
                          <span>Chunk {source.chunk_index + 1}</span>
                        ) : null}
                        {formatSimilarity(source) ? <span>{formatSimilarity(source)}</span> : null}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
