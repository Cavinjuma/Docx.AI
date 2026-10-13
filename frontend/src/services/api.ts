// All HTTP access to the backend goes through this module.
// Development uses the Vite proxy; production defaults to the deployed API and can be overridden.
const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.PROD ? 'https://docx-ai-creh.vercel.app' : '')

export interface HealthResponse {
  status: string
  app: string
  version: string
  environment: string
}

export interface UserResponse {
  id: number
  email: string
  full_name: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

export interface DocumentUploadResponse {
  id: number
  user_id: number
  filename: string
  file_type: string
  file_size: number
  upload_date: string
  processing_status: string
}

export interface ConversationResponse {
  id: number
  user_id: number
  title: string
  created_at: string
}

export interface ConversationMessageResponse {
  id: number
  role: string
  content: string
  created_at: string
  citations: Array<{ text: string; score: number; source: string }>
}

export interface ConversationDetailResponse extends ConversationResponse {
  messages: ConversationMessageResponse[]
}

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    let detail = `Request to ${path} failed`
    try {
      const payload = (await response.json()) as { detail?: string }
      detail = payload.detail ?? detail
    } catch {
      // Ignore JSON parsing errors and keep the default message.
    }
    throw new ApiError(detail, response.status)
  }
  return (await response.json()) as T
}

export const getHealth = (signal?: AbortSignal): Promise<HealthResponse> =>
  request<HealthResponse>('/api/health', { signal })

export const registerUser = (payload: { email: string; full_name: string; password: string }): Promise<TokenResponse> =>
  request<TokenResponse>('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

export const loginUser = (payload: { email: string; password: string }): Promise<TokenResponse> =>
  request<TokenResponse>('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

export const getCurrentUser = (token: string): Promise<UserResponse> =>
  request<UserResponse>('/api/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  })

export const uploadDocument = (file: File, token: string): Promise<DocumentUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  return request<DocumentUploadResponse>('/api/documents/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })
}

export const createConversation = (title: string, token: string): Promise<ConversationResponse> =>
  request<ConversationResponse>('/api/conversations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ title }),
  })

export const listConversations = (token: string): Promise<ConversationResponse[]> =>
  request<ConversationResponse[]>('/api/conversations', {
    headers: { Authorization: `Bearer ${token}` },
  })

export const getConversation = (conversationId: number, token: string): Promise<ConversationDetailResponse> =>
  request<ConversationDetailResponse>(`/api/conversations/${conversationId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })

export const sendMessage = (
  conversationId: number,
  question: string,
  token: string,
): Promise<{ user: ConversationMessageResponse; assistant: ConversationMessageResponse }> =>
  request<{ user: ConversationMessageResponse; assistant: ConversationMessageResponse }>(
    `/api/conversations/${conversationId}/messages`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ question }),
    },
  )
