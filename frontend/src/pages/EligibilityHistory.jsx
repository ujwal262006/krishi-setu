import { useState, useEffect } from 'react'
import { getMyEligibilityResults } from '../api/eligibility'

export default function EligibilityHistory() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getMyEligibilityResults()
      .then((res) => setResults(res.data))
      .catch(() => setError('Could not load history.'))
      .finally(() => setLoading(false))
  }, [])

  const badge = (r) => {
    if (r === 'met') return 'bg-green-700 text-white'
    if (r === 'not_met') return 'bg-red-600 text-white'
    return 'bg-gray-500 text-white'
  }

  if (loading) return <div className="max-w-4xl mx-auto p-4 text-gray-500">Loading...</div>

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold text-green-800 mb-4">My Eligibility History</h1>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      {results.length === 0 ? (
        <p className="text-gray-500">No checks done yet.</p>
      ) : (
        <div className="space-y-3">
          {results.map((r) => (
            <div key={r.scheme_id} className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-semibold text-gray-800">Scheme #{r.scheme_id}</h3>
                <span className={`text-xs font-bold px-3 py-1 rounded-full ${badge(r.overall_result)}`}>
                  {r.overall_result?.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <p className="text-sm text-gray-600">{r.summary}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}