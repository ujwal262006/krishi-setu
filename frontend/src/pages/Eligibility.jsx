import { useState, useEffect } from 'react'
import { listSchemes } from '../api/schemes'
import { checkEligibility } from '../api/eligibility'

export default function Eligibility() {
  const [schemes, setSchemes] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadSchemes = async () => {
      try {
        const res = await listSchemes({ limit: 50 })
        setSchemes(res.data)
      } catch (err) {
        setError('Could not load schemes.')
      } finally {
        setLoading(false)
      }
    }
    loadSchemes()
  }, [])

  const toggleScheme = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const handleCheck = async () => {
    if (selectedIds.length === 0) {
      setError('Select at least one scheme.')
      return
    }
    setError('')
    setChecking(true)
    setResults(null)
    try {
      const res = await checkEligibility(selectedIds)
      setResults(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Eligibility check failed.')
    } finally {
      setChecking(false)
    }
  }

  const resultColor = (result) => {
    if (result === 'met') return 'bg-green-50 text-green-800 border-green-200'
    if (result === 'not_met') return 'bg-red-50 text-red-800 border-red-200'
    return 'bg-gray-50 text-gray-700 border-gray-200'
  }

  const overallBadge = (result) => {
    if (result === 'met' || result === 'eligible')
      return 'bg-green-700 text-white'
    if (result === 'not_met' || result === 'not_eligible')
      return 'bg-red-600 text-white'
    return 'bg-gray-500 text-white'
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold text-green-800 mb-4">Check Your Eligibility</h1>

      {loading ? (
        <p className="text-gray-500">Loading schemes...</p>
      ) : (
        <>
          <p className="text-sm text-gray-600 mb-3">Select schemes to check eligibility for:</p>
          <div className="grid sm:grid-cols-2 gap-3 mb-6">
            {schemes.map((scheme) => (
              <label
                key={scheme.id}
                className={`flex items-center gap-3 bg-white border rounded-xl p-3 cursor-pointer ${
                  selectedIds.includes(scheme.id) ? 'border-green-500 ring-1 ring-green-400' : 'border-gray-200'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.includes(scheme.id)}
                  onChange={() => toggleScheme(scheme.id)}
                  className="w-4 h-4 accent-green-700"
                />
                <span className="text-sm font-medium text-gray-800">{scheme.name}</span>
              </label>
            ))}
          </div>

          {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

          <button
            onClick={handleCheck}
            disabled={checking}
            className="bg-green-700 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-800 disabled:opacity-50"
          >
            {checking ? 'Checking...' : 'Check Eligibility'}
          </button>
        </>
      )}

      {results && (
        <div className="mt-8 space-y-4">
          <h2 className="text-lg font-bold text-green-800">Results</h2>
          {results.map((r) => {
            const scheme = schemes.find((s) => s.id === r.scheme_id)
            return (
              <div key={r.scheme_id} className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-800">{scheme?.name || `Scheme #${r.scheme_id}`}</h3>
                  <span className={`text-xs font-bold px-3 py-1 rounded-full ${overallBadge(r.overall_result)}`}>
                    {r.overall_result?.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">{r.summary}</p>
                <div className="space-y-2">
                  {Object.entries(r.criteria_results || {}).map(([criterion, detail]) => (
                    <div
                      key={criterion}
                      className={`text-sm border rounded-lg px-3 py-2 ${resultColor(detail.result)}`}
                    >
                      <span className="font-medium capitalize">{criterion.replace(/_/g, ' ')}: </span>
                      {detail.explanation}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}