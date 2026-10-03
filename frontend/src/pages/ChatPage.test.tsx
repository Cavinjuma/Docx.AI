import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ChatPage } from './ChatPage'

const tokenKey = 'ai-di-platform-token'
const createdAt = '2026-10-03T12:00:00Z'

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('ChatPage', () => {
  afterEach(() => {
    localStorage.clear()
    vi.unstubAllGlobals()
  })

  it('creates a conversation and submits the first question', async () => {
    localStorage.setItem(tokenKey, 'test-token')
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      const method = init?.method ?? 'GET'

      if (url === '/api/conversations' && method === 'GET') return jsonResponse([])
      if (url === '/api/conversations' && method === 'POST') {
        return jsonResponse({ id: 7, user_id: 3, title: 'New chat 1', created_at: createdAt }, 201)
      }
      if (url === '/api/conversations/7' && method === 'GET') {
        return jsonResponse({ id: 7, user_id: 3, title: 'New chat 1', created_at: createdAt, messages: [] })
      }
      if (url === '/api/conversations/7/messages' && method === 'POST') {
        return jsonResponse({
          user: { id: 11, role: 'user', content: 'What is geodesy?', created_at: createdAt, citations: [] },
          assistant: { id: 12, role: 'assistant', content: 'Geodesy is the science of measuring Earth.', created_at: createdAt, citations: [] },
        })
      }

      throw new Error(`Unexpected request: ${method} ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>,
    )

    const askButton = screen.getByRole('button', { name: 'Ask question' })
    expect(askButton).toBeDisabled()

    fireEvent.change(screen.getByLabelText('Ask a question'), { target: { value: 'What is geodesy?' } })
    expect(askButton).toBeEnabled()
    fireEvent.click(askButton)

    expect(await screen.findByText('Geodesy is the science of measuring Earth.')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/conversations', expect.objectContaining({ method: 'POST' }))
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/conversations/7/messages', expect.objectContaining({ method: 'POST' }))
    })
  })
})
