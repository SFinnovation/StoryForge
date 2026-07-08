// 房间 WebSocket 客户端 (docs/multiplayer-realtime-design §5 / §8)
// 特性：自动重连（指数退避）、心跳保活、按 seq 去重、事件订阅。
import { getStoredToken } from './client'

const WS_BASE = (() => {
  const httpBase = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  // 支持相对路径：基于当前页面推导 ws(s) origin
  const origin = window.location.origin.replace(/^http/, 'ws')
  const path = httpBase.replace(/^https?:\/\/[^/]+/, '').replace(/\/$/, '')
  if (/^https?:\/\//.test(httpBase)) {
    return httpBase.replace(/^http/, 'ws').replace(/\/$/, '')
  }
  return `${origin}${path}`
})()

export class RoomSocket {
  constructor(roomId, { onEvent, onStatus, onReconnect } = {}) {
    this.roomId = roomId
    this.onEvent = onEvent || (() => {})
    this.onStatus = onStatus || (() => {})
    this.onReconnect = onReconnect || (() => {})
    this.ws = null
    this.seenSeq = new Set()
    this.lastSeq = 0
    this.reconnectAttempts = 0
    this.heartbeatTimer = null
    this.closedByUser = false
    this._typingActive = false
    this._typingStopTimer = null
  }

  connect() {
    const token = getStoredToken()
    const url = `${WS_BASE}/ws/rooms/${this.roomId}?token=${encodeURIComponent(token || '')}`
    this.onStatus('connecting')
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      const isReconnect = this.reconnectAttempts > 0
      this.reconnectAttempts = 0
      this.onStatus('online')
      this._startHeartbeat()
      if (isReconnect) this.onReconnect(this.lastSeq)
    }

    this.ws.onmessage = (raw) => {
      let event
      try {
        event = JSON.parse(raw.data)
      } catch {
        return
      }
      // 按 seq 去重（无 seq 的瞬时事件如 state.updated / pong 直接透传）
      if (typeof event.seq === 'number') {
        if (this.seenSeq.has(event.seq)) return
        this.seenSeq.add(event.seq)
        if (event.seq > this.lastSeq) this.lastSeq = event.seq
      }
      if (event.type === 'pong') return
      this.onEvent(event)
    }

    this.ws.onclose = () => {
      this._stopHeartbeat()
      if (this.closedByUser) {
        this.onStatus('offline')
        return
      }
      this.onStatus('reconnecting')
      this._scheduleReconnect()
    }

    this.ws.onerror = () => {
      try {
        this.ws.close()
      } catch {
        /* noop */
      }
    }
  }

  _scheduleReconnect() {
    this.reconnectAttempts += 1
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 15000)
    setTimeout(() => {
      if (!this.closedByUser) this.connect()
    }, delay)
  }

  _startHeartbeat() {
    this._stopHeartbeat()
    this.heartbeatTimer = setInterval(() => this.send('ping', {}), 25000)
  }

  _stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  send(type, data = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }))
      return true
    }
    return false
  }

  sendChat(content, clientMsgId) {
    return this.send('chat.send', { content, client_msg_id: clientMsgId })
  }

  sendOoc(content, clientMsgId) {
    return this.send('ooc.send', { content, client_msg_id: clientMsgId })
  }

  submitAction(actionText, clientMsgId) {
    return this.send('action.submit', { action_text: actionText, client_msg_id: clientMsgId })
  }

  sendDmAsk(question, clientMsgId, visibility = 'self') {
    return this.send('dm.ask', { question, client_msg_id: clientMsgId, visibility })
  }

  notifyTyping(active = true) {
    if (active) {
      if (!this._typingActive) {
        this._typingActive = true
        this.send('typing.start', {})
      }
      if (this._typingStopTimer) clearTimeout(this._typingStopTimer)
      this._typingStopTimer = setTimeout(() => this.notifyTyping(false), 3000)
      return true
    }
    if (this._typingStopTimer) {
      clearTimeout(this._typingStopTimer)
      this._typingStopTimer = null
    }
    if (this._typingActive) {
      this._typingActive = false
      this.send('typing.stop', {})
    }
    return true
  }

  close() {
    this.closedByUser = true
    this._stopHeartbeat()
    if (this.ws) {
      try {
        this.ws.close()
      } catch {
        /* noop */
      }
    }
  }
}

export const newClientMsgId = () =>
  `c_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
