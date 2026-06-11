const WS_BASE = import.meta.env.VITE_WS_BASE_URL || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`

export function createAppraisalSocket(dossierId, { onMessage, onReconnect } = {}) {
  let ws = null
  let retries = 0
  let closed = false
  const maxDelay = 30000

  const connect = () => {
    if (closed) return
    const url = `${WS_BASE}/ws/appraisal/${dossierId}`
    ws = new WebSocket(url)

    ws.onopen = () => {
      retries = 0
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage?.(data)
      } catch {
        onMessage?.({ type: 'raw', data: event.data })
      }
    }

    ws.onclose = () => {
      if (closed) return
      const delay = Math.min(1000 * 2 ** retries, maxDelay)
      retries += 1
      setTimeout(() => {
        onReconnect?.()
        connect()
      }, delay)
    }

    ws.onerror = () => ws?.close()
  }

  connect()

  return {
    close: () => {
      closed = true
      ws?.close()
    },
  }
}
