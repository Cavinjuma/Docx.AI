import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const health = { status: 'ok', app: 'AI Document Intelligence Platform', version: '0.1.0', environment: 'test' }

function mockFetch(impl: () => Promise<Response>) {
  vi.stubGlobal('fetch', vi.fn(impl))
}

describe('App', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('shows the backend status when the health check succeeds', async () => {
    mockFetch(() => Promise.resolve(new Response(JSON.stringify(health), { status: 200 })))
    render(<App />)
    expect(await screen.findByText(/Status: ok/)).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith('/api/health', expect.anything())
  })

  it('shows an error when the backend is unreachable', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    mockFetch(() => Promise.reject(new TypeError('network down')))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/unreachable/i)
  })

  it('shows an error when the backend returns a non-2xx status', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    mockFetch(() => Promise.resolve(new Response('{}', { status: 500 })))
    render(<App />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
