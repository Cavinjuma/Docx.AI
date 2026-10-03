import { type ChangeEvent, type DragEvent, type FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useHealth } from '../hooks/useHealth'
import { getCurrentUser, loginUser, registerUser, uploadDocument, type UserResponse } from '../services/api'

const AUTH_STORAGE_KEY = 'ai-di-platform-token'
const SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']

export function HomePage() {
  const health = useHealth()
  const navigate = useNavigate()
  const [authMode, setAuthMode] = useState<'login' | 'register'>('register')
  const [fullName, setFullName] = useState('Demo User')
  const [email, setEmail] = useState('demo@example.com')
  const [password, setPassword] = useState('StrongPassword123!')
  const [showPassword, setShowPassword] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(AUTH_STORAGE_KEY))
  const [user, setUser] = useState<UserResponse | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isDraggingFile, setIsDraggingFile] = useState(false)
  const [recentUploads, setRecentUploads] = useState<Array<{ filename: string; file_size: number }>>([])
  const [uploadState, setUploadState] = useState<{ phase: 'idle' | 'uploading' | 'success' | 'error'; message?: string }>({
    phase: 'idle',
  })

  useEffect(() => {
    if (!token) {
      setUser(null)
      return
    }

    getCurrentUser(token)
      .then((currentUser) => setUser(currentUser))
      .catch(() => {
        localStorage.removeItem(AUTH_STORAGE_KEY)
        setToken(null)
      })
  }, [token])

  async function handleAuthSubmit(event: FormEvent) {
    event.preventDefault()
    setAuthBusy(true)
    setAuthError('')

    try {
      const response =
        authMode === 'register'
          ? await registerUser({ email, full_name: fullName, password })
          : await loginUser({ email, password })

      localStorage.setItem(AUTH_STORAGE_KEY, response.access_token)
      setToken(response.access_token)
      setUser(response.user)
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Authentication failed.')
    } finally {
      setAuthBusy(false)
    }
  }

  async function handleUploadSubmit(event: FormEvent) {
    event.preventDefault()
    if (!token || selectedFiles.length === 0) {
      setUploadState({ phase: 'error', message: 'Select a file and sign in before uploading.' })
      return
    }

    setUploadState({ phase: 'uploading' })
    const uploaded: Array<{ filename: string; file_size: number }> = []
    const failed: File[] = []
    let firstError = ''

    for (const file of selectedFiles) {
      try {
        const response = await uploadDocument(file, token)
        uploaded.push({ filename: response.filename, file_size: response.file_size })
      } catch (error) {
        failed.push(file)
        if (!firstError) firstError = error instanceof Error ? error.message : 'Upload failed.'
      }
    }

    if (uploaded.length > 0) {
      setRecentUploads((current) => [...uploaded, ...current].slice(0, 5))
    }
    setSelectedFiles(failed)
    const fileInput = document.getElementById('document-file') as HTMLInputElement | null
    if (fileInput) fileInput.value = ''
    setUploadState(
      failed.length > 0
        ? {
            phase: 'error',
            message: `${uploaded.length} uploaded; ${failed.length} failed. ${firstError} Retry the remaining files.`,
          }
        : {
            phase: 'success',
            message: `${uploaded.length} ${uploaded.length === 1 ? 'file' : 'files'} uploaded successfully.`,
          },
    )
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    selectFiles(Array.from(event.target.files ?? []))
  }

  function selectFiles(files: File[]) {
    if (files.length === 0) return

    const unsupported = files.filter((file) => {
      const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
      return !SUPPORTED_FILE_EXTENSIONS.includes(extension)
    })
    if (unsupported.length > 0) {
      setSelectedFiles([])
      setUploadState({
        phase: 'error',
        message: `Unsupported file type${unsupported.length === 1 ? '' : 's'}: ${unsupported.map((file) => file.name).join(', ')}. Choose PDF, DOCX, TXT, or Markdown (.md) files.`,
      })
      return
    }

    setSelectedFiles(files)
    setUploadState({ phase: 'idle' })
  }

  function handleFileDragOver(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    if (uploadState.phase !== 'uploading') setIsDraggingFile(true)
  }

  function handleFileDragLeave(event: DragEvent<HTMLLabelElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setIsDraggingFile(false)
  }

  function handleFileDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    setIsDraggingFile(false)
    if (uploadState.phase === 'uploading') return
    selectFiles(Array.from(event.dataTransfer.files))
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 p-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Docx.AI<br/><i>Your AI Document Intelligence Platform</i></h1>
        <p className="mt-2 text-slate-600">
          Upload documents, then ask questions and get answers grounded in your sources.
        </p>
      </header>

      <section aria-label="Backend status" className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">Backend</h2>
        {health.phase === 'loading' && <p className="mt-2">Checking…</p>}
        {health.phase === 'error' && (
          <p role="alert" className="mt-2 text-red-700">
            Backend unreachable. Is the API running?
          </p>
        )}
        {health.phase === 'ok' && (
          <p className="mt-2 text-emerald-700">
            Status: {health.data.status} · v{health.data.version} · {health.data.environment}
          </p>
        )}
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold">Account</h2>
          {user ? (
            <div className="mt-4 space-y-3">
              <p className="text-sm text-slate-600">Signed in as</p>
              <p className="font-medium">{user.full_name}</p>
              <p className="text-sm text-slate-500">{user.email}</p>
              <button
                type="button"
                className="mt-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400"
                onClick={() => {
                  localStorage.removeItem(AUTH_STORAGE_KEY)
                  setToken(null)
                  setUser(null)
                }}
              >
                Sign out
              </button>
            </div>
          ) : (
            <form className="mt-4 space-y-3" onSubmit={handleAuthSubmit}>
              <div className="flex rounded-md border border-slate-200 p-1 text-sm">
                <button
                  type="button"
                  className={`flex-1 rounded px-3 py-2 ${authMode === 'register' ? 'bg-slate-900 text-white' : 'text-slate-600'}`}
                  onClick={() => setAuthMode('register')}
                >
                  Register
                </button>
                <button
                  type="button"
                  className={`flex-1 rounded px-3 py-2 ${authMode === 'login' ? 'bg-slate-900 text-white' : 'text-slate-600'}`}
                  onClick={() => setAuthMode('login')}
                >
                  Login
                </button>
              </div>

              {authMode === 'register' && (
                <label className="block text-sm">
                  <span className="mb-1 block text-slate-600">Full name</span>
                  <input
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none ring-0 focus:border-slate-500"
                  />
                </label>
              )}

              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">Email</span>
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none ring-0 focus:border-slate-500"
                />
              </label>

              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">Password</span>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 pr-10 outline-none ring-0 focus:border-slate-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((previous) => !previous)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-700"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5 fill-none stroke-current stroke-2">
                        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    ) : (
                      <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5 fill-none stroke-current stroke-2">
                        <path d="M3 3l18 18" />
                        <path d="M10.58 10.59A2 2 0 0 0 13.41 13.42" />
                        <path d="M9.88 5.08A10.94 10.94 0 0 1 12 5c6.5 0 10 7 10 7a17.6 17.6 0 0 1-3.2 4.6" />
                        <path d="M6.61 6.61A17.7 17.7 0 0 0 2 12s3.5 7 10 7a9.8 9.8 0 0 0 5.39-1.61" />
                      </svg>
                    )}
                  </button>
                </div>
              </label>

              {authError && <p className="text-sm text-red-700">{authError}</p>}

              <button
                type="submit"
                disabled={authBusy}
                className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {authBusy ? 'Working…' : authMode === 'register' ? 'Create account' : 'Sign in'}
              </button>
            </form>
          )}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold">Upload document</h2>
          {!token ? (
            <p className="mt-4 text-sm text-slate-600">Create an account or sign in before uploading a document.</p>
          ) : (
            <form className="mt-4 space-y-3" onSubmit={handleUploadSubmit}>
              <label
                htmlFor="document-file"
                onDragOver={handleFileDragOver}
                onDragLeave={handleFileDragLeave}
                onDrop={handleFileDrop}
                className={`flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-5 text-center transition ${isDraggingFile ? 'border-emerald-600 bg-emerald-50' : 'border-slate-300 bg-slate-50 hover:border-emerald-500 hover:bg-emerald-50/50'}`}
              >
                <input
                  id="document-file"
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  multiple
                  onChange={handleFileChange}
                  disabled={uploadState.phase === 'uploading'}
                  className="sr-only"
                  aria-label="Choose a document to upload"
                />
                <span className="text-sm font-medium text-slate-800">Drop a file here or click to choose</span>
                <span className="mt-1 text-xs text-slate-500">PDF, DOCX, TXT, or MD · select or drop multiple files</span>
                {selectedFiles.length > 0 && (
                  <span className="mt-3 max-w-full text-sm text-emerald-700">
                    {selectedFiles.length} {selectedFiles.length === 1 ? 'file' : 'files'} selected: {selectedFiles.map((file) => file.name).join(', ')}
                  </span>
                )}
              </label>

              <button
                type="submit"
                disabled={selectedFiles.length === 0 || uploadState.phase === 'uploading'}
                className="w-full rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {uploadState.phase === 'uploading' ? 'Uploading…' : `Upload ${selectedFiles.length > 0 ? `${selectedFiles.length} ` : ''}${selectedFiles.length === 1 ? 'document' : 'documents'}`}
              </button>

              {uploadState.phase !== 'idle' && (
                <>
                  <p
                    className={`text-sm ${uploadState.phase === 'success' ? 'text-emerald-700' : uploadState.phase === 'error' ? 'text-red-700' : 'text-slate-600'}`}
                  >
                    {uploadState.message}
                  </p>
                  {uploadState.phase === 'success' && (
                    <button
                      type="button"
                      onClick={() => navigate('/chat')}
                      className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
                    >
                      Open chat
                    </button>
                  )}
                </>
              )}
            </form>
          )}
        </section>
      </div>

      {recentUploads.length > 0 && (
        <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold">Recent uploads</h2>
          <ul className="mt-3 space-y-2">
            {recentUploads.map((upload) => (
              <li key={`${upload.filename}-${upload.file_size}`} className="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                <span className="truncate pr-3 text-slate-700">{upload.filename}</span>
                <span className="shrink-0 text-slate-500">{upload.file_size} bytes</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  )
}
