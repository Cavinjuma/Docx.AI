import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'

import {
  createConversation,
  getConversation,
  listConversations,
  sendMessage,
  type ConversationMessageResponse,
  type ConversationResponse,
} from '../services/api'

const AUTH_STORAGE_KEY = 'ai-di-platform-token'

export function ChatPage() {
  const token = localStorage.getItem(AUTH_STORAGE_KEY)
  const [conversations, setConversations] = useState<ConversationResponse[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ConversationMessageResponse[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) {
      setConversations([])
      setSelectedConversationId(null)
      setMessages([])
      return
    }

    listConversations(token)
      .then((items) => {
        setConversations(items)
        if (items.length > 0 && !selectedConversationId) {
          setSelectedConversationId(items[0].id)
        }
      })
      .catch(() => {
        setError('Unable to load your conversations.')
      })
  }, [token, selectedConversationId])

  useEffect(() => {
    if (!token || selectedConversationId === null) {
      setMessages([])
      return
    }

    getConversation(selectedConversationId, token)
      .then((conversation) => setMessages(conversation.messages))
      .catch(() => setError('Unable to load the selected conversation.'))
  }, [selectedConversationId, token])

  const activeConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId) ?? null,
    [conversations, selectedConversationId],
  )

  async function handleCreateConversation(event: FormEvent) {
    event.preventDefault()
    if (!token) {
      setError('Sign in first to start a conversation.')
      return
    }

    const title = `New chat ${conversations.length + 1}`
    try {
      const conversation = await createConversation(title, token)
      setConversations((current) => [conversation, ...current])
      setSelectedConversationId(conversation.id)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create a conversation.')
    }
  }

  async function handleAskQuestion(event: FormEvent) {
    event.preventDefault()
    if (!token || !question.trim()) {
      setError('Type a question before sending.')
      return
    }

    setLoading(true)
    setError('')

    try {
      let conversationId = selectedConversationId
      if (conversationId === null) {
        const conversation = await createConversation(`New chat ${conversations.length + 1}`, token)
        conversationId = conversation.id
        setConversations((current) => [conversation, ...current])
        setSelectedConversationId(conversation.id)
      }

      const response = await sendMessage(conversationId, question.trim(), token)
      setMessages((current) => [...current, response.user, response.assistant])
      setQuestion('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to send the message.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-4 p-6">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-semibold">Chat</h1>
          <p className="mt-2 text-slate-600">Sign in from the home page to start a grounded conversation.</p>
          <Link to="/" className="mt-4 inline-flex rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white">
            Go to home
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl gap-6 p-6">
      <aside className="w-80 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Conversations</h2>
          <button
            type="button"
            onClick={handleCreateConversation}
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
          >
            New
          </button>
        </div>

        <div className="mt-4 space-y-2">
          {conversations.length === 0 && <p className="text-sm text-slate-500">No conversations yet.</p>}
          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              onClick={() => setSelectedConversationId(conversation.id)}
              className={`w-full rounded-md border px-3 py-2 text-left text-sm ${
                conversation.id === selectedConversationId
                  ? 'border-slate-900 bg-slate-900 text-white'
                  : 'border-slate-200 bg-slate-50 text-slate-700'
              }`}
            >
              {conversation.title}
            </button>
          ))}
        </div>
      </aside>

      <section className="flex flex-1 flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
          <div>
            <h1 className="text-xl font-semibold">{activeConversation?.title ?? 'Conversation'}</h1>
            <p className="text-sm text-slate-500">Grounded answers from your uploaded documents</p>
          </div>
          <Link to="/" className="text-sm font-medium text-slate-700 hover:text-slate-900">
            Back to home
          </Link>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto">
          {messages.length === 0 && (
            <div className="rounded-md border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Ask a question about the documents you uploaded to begin.
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`rounded-lg border p-3 ${message.role === 'user' ? 'bg-slate-100 border-slate-200' : 'bg-emerald-50 border-emerald-200'}`}>
              <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">{message.role}</div>
              <p className="whitespace-pre-wrap text-sm text-slate-700">{message.content}</p>
              {message.citations.length > 0 && (
                <div className="mt-3 rounded-md border border-emerald-200 bg-white p-2 text-xs text-slate-600">
                  <div className="font-medium text-emerald-700">Sources</div>
                  <ul className="mt-1 list-disc space-y-1 pl-4">
                    {message.citations.map((citation) => (
                      <li key={`${message.id}-${citation.source}-${citation.text}`}>
                        {citation.source}: {citation.text}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>

        <form onSubmit={handleAskQuestion} className="mt-4 border-t border-slate-200 pt-4">
          <label htmlFor="chat-question" className="block text-sm font-medium text-slate-700">Ask a question</label>
          <textarea
            id="chat-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={4}
            className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500"
            placeholder="Ask about leave policy, expenses, or any uploaded document..."
          />
          {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="mt-3 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Thinking…' : 'Ask question'}
          </button>
        </form>
      </section>
    </main>
  )
}
