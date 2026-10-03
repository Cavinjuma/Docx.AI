import { useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from '../services/api'

export type HealthState =
  | { phase: 'loading' }
  | { phase: 'ok'; data: HealthResponse }
  | { phase: 'error' }

export function useHealth(): HealthState {
  const [state, setState] = useState<HealthState>({ phase: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    getHealth(controller.signal)
      .then((data) => setState({ phase: 'ok', data }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          console.error('Health check failed', error)
          setState({ phase: 'error' })
        }
      })
    return () => controller.abort()
  }, [])

  return state
}
