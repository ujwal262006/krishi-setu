import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getScheme } from '../api/schemes'

function formatValue(value) {
  if (Array.isArray(value)) {
    return value.map((v) => String(v).replace(/_/g, ' ')).join(', ')
  }
  if (typeof value === 'object' && value !== null) {
    return Object.entries(value)
      .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`)
      .join(', ')
  }
  return String(value)
}

export default function SchemeDetail() {
  const { id } = useParams()
  const [scheme, setScheme] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getScheme(id)
      .then((res) => setScheme(res.data))
      .catch(() => setError('Scheme not found.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="max-w-3xl mx-auto p-4 text-gray-500">Loading...</div>
  if (error || !scheme) return <div className="max-w-3xl mx-auto p-4 text-red-600">{error}</div>

  const criteria = scheme.eligibility_criteria || {}
  const benefits = scheme.benefits || {}
  const hasCriteria = Object.keys(criteria).length > 0
  const hasBenefits = Object.keys(benefits).length > 0

  return (
    <div className="max-w-3xl mx-auto p-4">
      <Link to="/browse" className="text-sm text-green-700 font-medium mb-4 inline-block">
        ← Back to Browse
      </Link>

      <div className="bg-white rounded-2xl shadow-sm p-6">
        <h1 className="text-2xl font-bold text-green-800">{scheme.name}</h1>
        {scheme.name_hindi && <p className="text-gray-500 mt-1">{scheme.name_hindi}</p>}

        {scheme.description && (
          <p className="text-gray-700 mt-4 leading-relaxed">{scheme.description}</p>
        )}

        {hasBenefits && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">Benefits</h2>
            <div className="bg-green-50 rounded-lg p-4 space-y-2">
              {Object.entries(benefits).map(([key, value]) => (
                <p key={key} className="text-sm text-gray-700 break-words">
                  <span className="font-medium capitalize">{key.replace(/_/g, ' ')}: </span>
                  {formatValue(value)}
                </p>
              ))}
            </div>
          </div>
        )}

        {hasCriteria && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">Eligibility Criteria</h2>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              {Object.entries(criteria).map(([key, value]) => (
                <p key={key} className="text-sm text-gray-700 break-words">
                  <span className="font-medium capitalize">{key.replace(/_/g, ' ')}: </span>
                  {formatValue(value)}
                </p>
              ))}
            </div>
          </div>
        )}

        {!hasCriteria && (
          <p className="text-xs text-gray-400 mt-6">
            Detailed eligibility criteria not yet available for this scheme.
          </p>
        )}

        {scheme.application_url && (
          <a
            href={scheme.application_url}
            target="_blank"
            rel="noreferrer"
            className="inline-block mt-6 bg-green-700 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-800"
          >
            Apply Now →
          </a>
        )}
      </div>
    </div>
  )
}