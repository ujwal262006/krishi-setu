import { useState, useRef, useEffect } from 'react'
import { streamAssistantQuery } from '../api/assistant'

export default function Assistant() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => crypto.randomUUID())
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    const query = input.trim()
    if (!query || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: query }])
    setMessages((prev) => [...prev, { role: 'assistant', text: '' }])
    setLoading(true)

    try {
      await streamAssistantQuery(query, sessionId, (chunk) => {
        setMessages((prev) => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            role: 'assistant',
            text: updated[updated.length - 1].text + chunk,
          }
          return updated
        })
      })
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          text: 'Sorry, something went wrong. Please try again.',
        }
        return updated
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-4 flex flex-col h-[calc(100vh-64px)]">
      <h1 className="text-2xl font-bold text-green-800 mb-4">Ask Krishi Setu 🌾</h1>

      <div className="flex-1 overflow-y-auto bg-white rounded-xl border border-gray-200 p-4 mb-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-gray-400 text-sm text-center mt-10">
            Try asking: "tractor ke liye paisa" or "PM-KISAN kya hai"
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap ${
              m.role === 'user'
                ? 'bg-green-700 text-white ml-auto rounded-br-sm'
                : 'bg-gray-100 text-gray-800 mr-auto rounded-bl-sm'
            }`}
          >
            {m.text || (loading && i === messages.length - 1 ? '...' : '')}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question..."
          disabled={loading}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-green-700 text-white px-5 py-2 rounded-lg font-medium hover:bg-green-800 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  )
}