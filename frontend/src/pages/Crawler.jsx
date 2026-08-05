import { useState, useEffect } from 'react'
import { listSourcesAdmin, listCrawlJobsAdmin, triggerCrawlAdmin } from '../api/admin'

export default function Crawler() {
  const [sources, setSources] = useState([])
  const [jobs, setJobs] = useState([])
  const [error, setError] = useState('')
  const [triggering, setTriggering] = useState(null)

  const load = async () => {
    try {
      const [srcRes, jobRes] = await Promise.all([
        listSourcesAdmin(),
        listCrawlJobsAdmin({ limit: 20 }),
      ])
      setSources(srcRes.data)
      setJobs(jobRes.data)
    } catch (err) {
      setError('Could not load crawler data.')
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleTrigger = async (sourceId) => {
    setTriggering(sourceId)
    try {
      await triggerCrawlAdmin(sourceId)
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to trigger crawl.')
    } finally {
      setTriggering(null)
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold text-green-800 mb-6">Crawler</h1>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <h2 className="text-lg font-semibold text-gray-800 mb-3">Sources</h2>
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto mb-8">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Last Crawled</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{s.name}</td>
                <td className="px-4 py-2">{s.is_active ? 'Active' : 'Inactive'}</td>
                <td className="px-4 py-2">{s.last_crawled_at ? new Date(s.last_crawled_at).toLocaleString() : 'Never'}</td>
                <td className="px-4 py-2">
                  <button
                    onClick={() => handleTrigger(s.id)}
                    disabled={triggering === s.id}
                    className="text-green-700 font-medium text-sm hover:underline disabled:opacity-50"
                  >
                    {triggering === s.id ? 'Triggering...' : 'Trigger Crawl'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="text-lg font-semibold text-gray-800 mb-3">Recent Jobs</h2>
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-2">ID</th>
              <th className="px-4 py-2">Source</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">URLs Crawled</th>
              <th className="px-4 py-2">Errors</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{j.id}</td>
                <td className="px-4 py-2">{j.source_id}</td>
                <td className="px-4 py-2">{j.status}</td>
                <td className="px-4 py-2">{j.urls_crawled}</td>
                <td className="px-4 py-2">{j.errors_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}