const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')

const TOKEN_KEY = 'storyforge_access_token'
const USER_KEY = 'storyforge_user'

const FIELD_LABELS = {
  username: '用户名',
  password: '密码',
  nickname: '昵称',
  action_text: '行动内容',
  name: '名称',
  title: '标题',
  difficulty: '挑战难度'
}

const getFieldLabel = (loc) => {
  if (!Array.isArray(loc)) return '请求参数'
  const fieldPath = loc.filter((part) => part !== 'body' && part !== 'query' && part !== 'path')
  const field = String(fieldPath[fieldPath.length - 1] || '')
  return FIELD_LABELS[field] || field || '请求参数'
}

const formatValidationIssue = (issue) => {
  if (typeof issue === 'string') return issue
  if (!issue || typeof issue !== 'object') return ''

  const label = getFieldLabel(issue.loc)
  const context = issue.ctx || {}

  if (issue.type === 'missing') {
    return `请填写${label}`
  }
  if (issue.type === 'string_too_short') {
    return `${label}至少需要 ${context.min_length || 1} 个字符`
  }
  if (issue.type === 'string_too_long') {
    return `${label}不能超过 ${context.max_length || '限制'} 个字符`
  }
  if (issue.type === 'greater_than_equal') {
    return `${label}不能小于 ${context.ge}`
  }
  if (issue.type === 'less_than_equal') {
    return `${label}不能大于 ${context.le}`
  }

  return issue.msg ? `${label}：${issue.msg}` : `${label}格式不正确`
}

const formatErrorMessage = (message) => {
  if (!message) return ''
  if (typeof message === 'string') return message
  if (Array.isArray(message)) {
    return message.map(formatValidationIssue).filter(Boolean).join('；')
  }
  if (typeof message === 'object') {
    return formatErrorMessage(message.message || message.detail || message.msg) || JSON.stringify(message)
  }
  return String(message)
}

const getPayloadErrorMessage = (payload, fallback) =>
  formatErrorMessage(payload?.message) || formatErrorMessage(payload?.detail) || fallback

export class ApiError extends Error {
  constructor(message, { status = 0, code = 0, data = null } = {}) {
    super(formatErrorMessage(message) || '请求失败')
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.data = data
  }
}

export const getStoredToken = () => localStorage.getItem(TOKEN_KEY)

export const getStoredUser = () => {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const storeAuth = ({ access_token: accessToken, user }) => {
  if (accessToken) {
    localStorage.setItem(TOKEN_KEY, accessToken)
  }
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

export const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

const parseResponse = async (response) => {
  const text = await response.text()
  if (!text) return null

  try {
    return JSON.parse(text)
  } catch {
    throw new ApiError('后端返回了无法解析的数据', {
      status: response.status,
      data: text
    })
  }
}

export const apiRequest = async (path, options = {}) => {
  const { method = 'GET', body, headers = {}, auth = true } = options
  const token = getStoredToken()
  const requestHeaders = {
    Accept: 'application/json',
    ...headers
  }

  const init = {
    method,
    headers: requestHeaders
  }

  if (auth && token) {
    requestHeaders.Authorization = `Bearer ${token}`
  }

  if (body !== undefined) {
    requestHeaders['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, init)
  const payload = await parseResponse(response)

  if (!response.ok) {
    throw new ApiError(getPayloadErrorMessage(payload, `请求失败：${response.status}`), {
      status: response.status,
      code: payload?.code,
      data: payload
    })
  }

  if (payload && typeof payload.code === 'number' && payload.code !== 0) {
    throw new ApiError(payload.message || '请求失败', {
      status: response.status,
      code: payload.code,
      data: payload.data
    })
  }

  return payload?.data ?? payload
}

const withAuth = (payload) => {
  storeAuth(payload)
  return payload
}

export const authApi = {
  register: (payload) => apiRequest('/auth/register', { method: 'POST', body: payload, auth: false }).then(withAuth),
  login: (payload) => apiRequest('/auth/login', { method: 'POST', body: payload, auth: false }).then(withAuth),
  guest: () => apiRequest('/auth/guest', { method: 'POST', auth: false }).then(withAuth),
  me: () => apiRequest('/auth/me'),
  logout: async () => {
    try {
      if (getStoredToken()) await apiRequest('/auth/logout', { method: 'POST' })
    } finally {
      clearAuth()
    }
  }
}

export const rulesApi = {
  dnd5eSummary: () => apiRequest('/rules/dnd5e/summary', { auth: false }),
  dnd5eSkills: () => apiRequest('/rules/dnd5e/skills', { auth: false })
}

export const worldsApi = {
  list: () => apiRequest('/worlds', { auth: false }),
  get: (worldId) => apiRequest(`/worlds/${worldId}`, { auth: false })
}

export const charactersApi = {
  list: () => apiRequest('/characters'),
  get: (characterId) => apiRequest(`/characters/${characterId}`),
  create: (payload) => apiRequest('/characters', { method: 'POST', body: payload })
}

export const roomsApi = {
  list: ({ scope = 'mine' } = {}) => apiRequest(`/rooms?scope=${encodeURIComponent(scope)}`),
  get: (roomId) => apiRequest(`/rooms/${roomId}`),
  create: (payload) => apiRequest('/rooms', { method: 'POST', body: payload }),
  join: (payload) => apiRequest('/rooms/join', { method: 'POST', body: payload }),
  leave: (roomId) => apiRequest(`/rooms/${roomId}/leave`, { method: 'POST' }),
  setReady: (roomId, isReady) =>
    apiRequest(`/rooms/${roomId}/ready`, { method: 'POST', body: { is_ready: isReady } }),
  setCharacter: (roomId, characterId) =>
    apiRequest(`/rooms/${roomId}/character`, { method: 'POST', body: { character_id: characterId } }),
  start: (roomId, characterId = null) =>
    apiRequest(`/rooms/${roomId}/start`, { method: 'POST', body: { character_id: characterId } }),
  end: (roomId) => apiRequest(`/rooms/${roomId}/end`, { method: 'POST' }),
  messages: (roomId, { beforeSeq = null, afterSeq = null, limit = 50 } = {}) => {
    const params = new URLSearchParams()
    if (beforeSeq != null) params.set('before_seq', String(beforeSeq))
    if (afterSeq != null) params.set('after_seq', String(afterSeq))
    params.set('limit', String(limit))
    return apiRequest(`/rooms/${roomId}/messages?${params.toString()}`)
  },
  chat: (roomId, content, clientMsgId = null) =>
    apiRequest(`/rooms/${roomId}/chat`, {
      method: 'POST',
      body: { content, client_msg_id: clientMsgId }
    }),
  ooc: (roomId, content, clientMsgId = null) =>
    apiRequest(`/rooms/${roomId}/ooc`, {
      method: 'POST',
      body: { content, client_msg_id: clientMsgId }
    }),
  action: (roomId, actionText, clientMsgId = null) =>
    apiRequest(`/rooms/${roomId}/action`, {
      method: 'POST',
      body: { action_text: actionText, client_msg_id: clientMsgId }
    }),
  ask: (roomId, question, { clientMsgId = null, visibility = 'self' } = {}) =>
    apiRequest(`/rooms/${roomId}/ask`, {
      method: 'POST',
      body: { question, client_msg_id: clientMsgId, visibility }
    })
}

export const sessionsApi = {
  list: () => apiRequest('/sessions'),
  get: (sessionId) => apiRequest(`/sessions/${sessionId}`),
  start: (payload) => apiRequest('/sessions/start', { method: 'POST', body: payload }),
  messages: (sessionId) => apiRequest(`/sessions/${sessionId}/messages`),
  action: (sessionId, actionText) =>
    apiRequest(`/sessions/${sessionId}/action`, { method: 'POST', body: { action_text: actionText } }),
  end: (sessionId) => apiRequest(`/sessions/${sessionId}/end`, { method: 'POST' }),
  delete: (sessionId) => apiRequest(`/sessions/${sessionId}`, { method: 'DELETE' }),
  generateReport: (sessionId) => apiRequest(`/sessions/${sessionId}/report/generate`, { method: 'POST' }),
  report: (sessionId) => apiRequest(`/sessions/${sessionId}/report`)
}

const toQueryString = (params = {}) => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, String(value))
    }
  })
  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

export const adminApi = {
  summary: () => apiRequest('/admin/summary'),
  worlds: ({ includeDisabled = true } = {}) =>
    apiRequest(`/admin/worlds${toQueryString({ include_disabled: includeDisabled })}`),
  sessions: (params = {}) => apiRequest(`/admin/sessions${toQueryString(params)}`),
  users: (params = {}) => apiRequest(`/admin/users${toQueryString(params)}`),
  createWorld: (payload) => apiRequest('/admin/worlds', { method: 'POST', body: payload }),
  enableWorld: (worldId) => apiRequest(`/admin/worlds/${worldId}/enable`, { method: 'POST' }),
  deleteWorld: (worldId) => apiRequest(`/admin/worlds/${worldId}`, { method: 'DELETE' }),
  createModule: (worldId, payload) => apiRequest(`/admin/worlds/${worldId}/modules`, { method: 'POST', body: payload }),
  enableModule: (moduleId) => apiRequest(`/admin/modules/${moduleId}/enable`, { method: 'POST' }),
  deleteModule: (moduleId) => apiRequest(`/admin/modules/${moduleId}`, { method: 'DELETE' }),
  dissolveSession: (sessionId, payload = {}) =>
    apiRequest(`/admin/sessions/${sessionId}/dissolve`, { method: 'POST', body: payload }),
  banUser: (userId, payload = {}) => apiRequest(`/admin/users/${userId}/ban`, { method: 'POST', body: payload }),
  unbanUser: (userId, payload = {}) => apiRequest(`/admin/users/${userId}/unban`, { method: 'POST', body: payload })
}
