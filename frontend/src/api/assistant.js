import api from './axiosInstance'

export const askAssistant = (query, sessionId) =>
  api.post('/assistant/query', { query, session_id: sessionId })

export const searchAssistantPublic = (q, limit = 5) =>
  api.get('/assistant/search', { params: { q, limit } })

export async function streamAssistantQuery(query, sessionId, onChunk) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL
  const params = new URLSearchParams({ q: query })
  if (sessionId) params.append('session_id', sessionId)

  const response = await fetch(`${baseUrl}/assistant/query/stream?${params}`)

  if (!response.ok || !response.body) {
    throw new Error('Stream request failed')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value, { stream: true })
    onChunk(chunk)
  }
}