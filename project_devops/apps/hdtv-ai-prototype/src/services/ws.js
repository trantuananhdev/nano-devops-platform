/**
 * WebSocket service — HDTV AI Platform
 *
 * Provides a singleton general-purpose WS connection + per-appraisal connections.
 * Message format: { type: string, data: object, timestamp: string }
 */

const WS_BASE = import.meta.env.VITE_WS_BASE_URL
  || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`

const TOKEN_KEY = 'hdtv_access_token'

// ============================================================
// Per-appraisal socket (legacy, used by dossier appraise flow)
// ============================================================
export function createAppraisalSocket(dossierId, { onMessage, onReconnect } = {}) {
  let ws = null
  let retries = 0
  let closed = false
  const MAX_RETRIES = 5
  const MAX_DELAY = 30000

  const connect = () => {
    if (closed) return
    const token = localStorage.getItem(TOKEN_KEY)
    const url = `${WS_BASE}/ws/appraisal/${dossierId}${token ? `?token=${token}` : ''}`
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
      if (retries >= MAX_RETRIES) {
        console.warn(`[WS] Max retries (${MAX_RETRIES}) reached for dossier ${dossierId}`)
        return
      }
      const delay = Math.min(1000 * 2 ** retries, MAX_DELAY)
      retries += 1
      setTimeout(() => {
        onReconnect?.()
        connect()
      }, delay)
    }

    ws.onerror = () => ws?.close()
  }

  connect()
  return { close: () => { closed = true; ws?.close() } }
}

// ============================================================
// General-purpose singleton WS — broadcasts all platform events
// ============================================================
let _mainWs = null
let _mainStatus = 'disconnected'  // 'connected' | 'connecting' | 'disconnected'
let _mainListeners = new Map()    // eventType → Set<callback>
let _globalListeners = new Set()  // catch-all callbacks
let _mainRetries = 0
let _mainClosed = false
const MAIN_MAX_RETRIES = 5

function _connectMain() {
  if (_mainClosed) return
  _mainStatus = 'connecting'
  _notifyStatusChange()

  const token = localStorage.getItem(TOKEN_KEY)
  const url = `${WS_BASE}/ws${token ? `?token=${token}` : ''}`
  _mainWs = new WebSocket(url)

  _mainWs.onopen = () => {
    _mainStatus = 'connected'
    _mainRetries = 0
    _notifyStatusChange()
  }

  _mainWs.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      // Notify type-specific listeners
      const typeListeners = _mainListeners.get(msg.type)
      if (typeListeners) {
        typeListeners.forEach(cb => cb(msg.data, msg))
      }
      // Notify global listeners
      _globalListeners.forEach(cb => cb(msg))
    } catch {
      /* ignore malformed messages */
    }
  }

  _mainWs.onclose = () => {
    _mainStatus = 'disconnected'
    _notifyStatusChange()
    if (_mainClosed) return
    if (_mainRetries >= MAIN_MAX_RETRIES) return
    const delay = Math.min(1000 * 2 ** _mainRetries, 30000)
    _mainRetries++
    setTimeout(_connectMain, delay)
  }

  _mainWs.onerror = () => _mainWs?.close()
}

function _notifyStatusChange() {
  const statusListeners = _mainListeners.get('__status__')
  if (statusListeners) {
    statusListeners.forEach(cb => cb(_mainStatus))
  }
}

export const mainWs = {
  /** Initialize the main WS connection. Call once in App.vue onMounted. */
  connect() {
    if (_mainWs && _mainWs.readyState <= 1) return // already open or connecting
    _mainClosed = false
    _connectMain()
  },

  disconnect() {
    _mainClosed = true
    _mainWs?.close()
    _mainStatus = 'disconnected'
  },

  /** Subscribe to a specific event type. Returns an unsubscribe function. */
  on(eventType, callback) {
    if (!_mainListeners.has(eventType)) {
      _mainListeners.set(eventType, new Set())
    }
    _mainListeners.get(eventType).add(callback)
    return () => _mainListeners.get(eventType)?.delete(callback)
  },

  /** Subscribe to all messages. Returns an unsubscribe function. */
  onAny(callback) {
    _globalListeners.add(callback)
    return () => _globalListeners.delete(callback)
  },

  get status() {
    return _mainStatus
  },
}
