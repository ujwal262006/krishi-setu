import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listSchemes, searchSchemes } from '../api/schemes'

export default function Browse() {
  const [schemes, setSchemes] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadDefaultSchemes = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await listSchemes({ limit: 20 })
      setSchemes(res.data)
    } catch (err) {
      setError('Could not load schemes.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDefaultSchemes()
  }, [])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) {
      loadDefaultSchemes()
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await searchSchemes(query)
      setSchemes(res.data.results)
    } catch (err) {
      setError('Search failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold text-green-800 mb-4">Browse Schemes</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search e.g. tractor ke liye paisa"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          type="submit"
          className="bg-green-700 text-white px-5 py-2 rounded-lg font-medium hover:bg-green-800"
        >
          Search
        </button>
      </form>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {loading ? (
        <p className="text-gray-500">Loading schemes...</p>
      ) : schemes.length === 0 ? (
        <p className="text-gray-500">No schemes found.</p>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {schemes.map((scheme) => (
            <Link
              key={scheme.id}
              to={`/schemes/${scheme.id}`}
              className="bg-white rounded-xl shadow-sm p-4 border border-gray-100 hover:border-green-300 transition block"
            >
              <h2 className="font-semibold text-green-800">{scheme.name}</h2>
              {scheme.name_hindi && <p className="text-sm text-gray-500">{scheme.name_hindi}</p>}
              <p className="text-sm text-gray-600 mt-2">
                {scheme.description ? scheme.description.slice(0, 150) : 'No description available.'}
              </p>
              <span className="text-green-700 text-sm font-medium mt-2 inline-block">
                View Details →
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}