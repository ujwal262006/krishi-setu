import { useState, useEffect } from 'react'
import {
  listSourcesAdmin,
  listCrawlJobsAdmin,
  triggerCrawlAdmin,
  getCrawlJobDetail,
  getSourceJobs,
} from '../api/admin'

export default function Crawler() {
  const [sources, setSources] = useState([])
  const [jobs, setJobs] = useState([])
  const [error, setError] = useState('')
  const [triggering, setTriggering] = useState(null)
  const [selectedJob, setSelectedJob] = useState(null)
  const [sourceJobsView, setSourceJobsView] = useState(null)

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

  const handleViewJob = async (jobId) => {
    try {
      const res = await getCrawlJobDetail(jobId)
      setSelectedJob(res.data)
    } catch (err) {
      setError('Could not load job detail.')
    }
  }

  const handleViewSourceJobs = async (source) => {
    try {
      const res = await getSourceJobs(source.id)
      setSourceJobsView({ source, jobs: res.data })
    } catch (err) {
      setError('Could not load jobs for this source.')
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
                <td className="px-4 py-2 flex gap-3">
                  <button
                    onClick={() => handleTrigger(s.id)}
                    disabled={triggering === s.id}
                    className="text-green-700 font-medium text-sm hover:underline disabled:opacity-50"
                  >
                    {triggering === s.id ? 'Triggering...' : 'Trigger Crawl'}
                  </button>
                  <button
                    onClick={() => handleViewSourceJobs(s)}
                    className="text-blue-600 font-medium text-sm hover:underline"
                  >
                    View Jobs
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sourceJobsView && (
        <div className="bg-white border border-blue-200 rounded-xl p-4 mb-8">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-gray-800">Jobs for: {sourceJobsView.source.name}</h3>
            <button onClick={() => setSourceJobsView(null)} className="text-sm text-gray-500 hover:underline">
              Close
            </button>
          </div>
          {sourceJobsView.jobs.length === 0 ? (
            <p className="text-sm text-gray-500">No jobs for this source yet.</p>
          ) : (
            <div className="space-y-2">
              {sourceJobsView.jobs.map((j) => (
                <div key={j.id} className="text-sm border border-gray-100 rounded-lg px-3 py-2 flex justify-between">
                  <span>Job #{j.id} — {j.status}</span>
                  <button onClick={() => handleViewJob(j.id)} className="text-green-700 hover:underline">
                    View Detail
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <h2 className="text-lg font-semibold text-gray-800 mb-3">Recent Jobs</h2>
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto mb-8">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-2">ID</th>
              <th className="px-4 py-2">Source</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">URLs Crawled</th>
              <th className="px-4 py-2">Errors</th>
              <th className="px-4 py-2"></th>
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
                <td className="px-4 py-2">
                  <button onClick={() => handleViewJob(j.id)} className="text-blue-600 hover:underline">
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedJob && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setSelectedJob(null)}>
          <div className="bg-white rounded-xl p-6 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-800">Job #{selectedJob.id}</h3>
              <button onClick={() => setSelectedJob(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="space-y-2 text-sm text-gray-700">
              <p><span className="font-medium">Source ID:</span> {selectedJob.source_id}</p>
              <p><span className="font-medium">Status:</span> {selectedJob.status}</p>
              <p><span className="font-medium">Type:</span> {selectedJob.job_type}</p>
              <p><span className="font-medium">URLs Discovered:</span> {selectedJob.urls_discovered}</p>
              <p><span className="font-medium">URLs Crawled:</span> {selectedJob.urls_crawled}</p>
              <p><span className="font-medium">Schemes Upserted:</span> {selectedJob.schemes_upserted}</p>
              <p><span className="font-medium">Errors:</span> {selectedJob.errors_count}</p>
              <p><span className="font-medium">Attempts:</span> {selectedJob.attempts}</p>
              <p><span className="font-medium">Started:</span> {selectedJob.started_at ? new Date(selectedJob.started_at).toLocaleString() : '—'}</p>
              <p><span className="font-medium">Completed:</span> {selectedJob.completed_at ? new Date(selectedJob.completed_at).toLocaleString() : '—'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}