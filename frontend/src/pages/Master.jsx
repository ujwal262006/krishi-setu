import { useState, useEffect } from 'react'
import {
  listMinistriesAdmin,
  createMinistryAdmin,
  updateMinistry,
  deleteMinistry,
  listSourcesAdmin,
  createSourceAdmin,
  updateSourceAdmin,
  deleteSourceAdmin,
} from '../api/admin'

const emptyMinistry = { name: '', name_hindi: '', acronym: '', website_url: '' }
const emptySource = {
  name: '', base_url: '', format: 'html', crawl_interval_hours: 24,
  max_depth: 3, rate_limit_rps: 1.0, ministry_id: '',
}

export default function Master() {
  const [ministries, setMinistries] = useState([])
  const [sources, setSources] = useState([])
  const [error, setError] = useState('')

  const [showMinistryForm, setShowMinistryForm] = useState(false)
  const [ministryForm, setMinistryForm] = useState(emptyMinistry)
  const [editingMinistryId, setEditingMinistryId] = useState(null)
  const [savingMinistry, setSavingMinistry] = useState(false)

  const [showSourceForm, setShowSourceForm] = useState(false)
  const [sourceForm, setSourceForm] = useState(emptySource)
  const [editingSourceId, setEditingSourceId] = useState(null)
  const [savingSource, setSavingSource] = useState(false)

  const loadAll = async () => {
    try {
      const [m, s] = await Promise.all([listMinistriesAdmin(), listSourcesAdmin()])
      setMinistries(m.data)
      setSources(s.data)
    } catch (err) {
      setError('Could not load master data.')
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  // ── Ministry handlers ──────────────────────────────────────────────
  const startEditMinistry = (m) => {
    setMinistryForm({
      name: m.name || '',
      name_hindi: m.name_hindi || '',
      acronym: m.acronym || '',
      website_url: m.website_url || '',
    })
    setEditingMinistryId(m.id)
    setShowMinistryForm(true)
  }

  const resetMinistryForm = () => {
    setMinistryForm(emptyMinistry)
    setEditingMinistryId(null)
    setShowMinistryForm(false)
  }

  const handleMinistrySubmit = async (e) => {
    e.preventDefault()
    setSavingMinistry(true)
    setError('')
    try {
      const payload = {
        name: ministryForm.name,
        name_hindi: ministryForm.name_hindi || null,
        acronym: ministryForm.acronym || null,
        website_url: ministryForm.website_url || null,
      }
      if (editingMinistryId) {
        await updateMinistry(editingMinistryId, payload)
      } else {
        await createMinistryAdmin(payload)
      }
      resetMinistryForm()
      await loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save ministry.')
    } finally {
      setSavingMinistry(false)
    }
  }

  const handleDeleteMinistry = async (id) => {
    if (!confirm('Delete this ministry? This cannot be undone.')) return
    try {
      await deleteMinistry(id)
      await loadAll()
    } catch (err) {
      setError('Failed to delete ministry (it may have linked schemes or sources).')
    }
  }

  // ── Source handlers ────────────────────────────────────────────────
  const startEditSource = (source) => {
    setSourceForm({
      name: source.name || '',
      base_url: source.base_url || '',
      format: source.format || 'html',
      crawl_interval_hours: source.crawl_interval_hours || 24,
      max_depth: source.max_depth || 3,
      rate_limit_rps: source.rate_limit_rps || 1.0,
      ministry_id: source.ministry_id || '',
    })
    setEditingSourceId(source.id)
    setShowSourceForm(true)
  }

  const resetSourceForm = () => {
    setSourceForm(emptySource)
    setEditingSourceId(null)
    setShowSourceForm(false)
  }

  const handleSourceSubmit = async (e) => {
    e.preventDefault()
    setSavingSource(true)
    setError('')
    try {
      const payload = {
        name: sourceForm.name,
        base_url: sourceForm.base_url,
        format: sourceForm.format,
        crawl_interval_hours: parseInt(sourceForm.crawl_interval_hours),
        max_depth: parseInt(sourceForm.max_depth),
        rate_limit_rps: parseFloat(sourceForm.rate_limit_rps),
        ministry_id: sourceForm.ministry_id ? parseInt(sourceForm.ministry_id) : null,
      }
      if (editingSourceId) {
        await updateSourceAdmin(editingSourceId, payload)
      } else {
        await createSourceAdmin(payload)
      }
      resetSourceForm()
      await loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save source.')
    } finally {
      setSavingSource(false)
    }
  }

  const handleDeleteSource = async (id) => {
    if (!confirm('Delete this source? This cannot be undone.')) return
    try {
      await deleteSourceAdmin(id)
      await loadAll()
    } catch (err) {
      setError('Failed to delete source (it may have linked crawl jobs).')
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold text-green-800 mb-6">Master Data</h1>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {/* ── Ministries ── */}
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-gray-800">Ministries</h2>
        <button
          onClick={() => (showMinistryForm ? resetMinistryForm() : setShowMinistryForm(true))}
          className="bg-green-700 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-green-800"
        >
          {showMinistryForm ? 'Cancel' : '+ Add Ministry'}
        </button>
      </div>

      {showMinistryForm && (
        <form onSubmit={handleMinistrySubmit} className="bg-white border border-gray-200 rounded-xl p-4 mb-4 space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <input
              placeholder="Ministry Name *" required
              value={ministryForm.name}
              onChange={(e) => setMinistryForm({ ...ministryForm, name: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
            <input
              placeholder="Name (Hindi)"
              value={ministryForm.name_hindi}
              onChange={(e) => setMinistryForm({ ...ministryForm, name_hindi: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
            <input
              placeholder="Acronym"
              value={ministryForm.acronym}
              onChange={(e) => setMinistryForm({ ...ministryForm, acronym: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
            <input
              placeholder="Website URL"
              value={ministryForm.website_url}
              onChange={(e) => setMinistryForm({ ...ministryForm, website_url: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <button
            type="submit" disabled={savingMinistry}
            className="bg-green-700 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-green-800 disabled:opacity-50"
          >
            {savingMinistry ? 'Saving...' : editingMinistryId ? 'Update Ministry' : 'Create Ministry'}
          </button>
        </form>
      )}

      <div className="grid sm:grid-cols-2 gap-3 mb-8">
        {ministries.map((m) => (
          <div key={m.id} className="bg-white border border-gray-200 rounded-xl p-3">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-medium text-gray-800">{m.name}</p>
                {m.name_hindi && <p className="text-sm text-gray-500">{m.name_hindi}</p>}
                {m.acronym && <p className="text-xs text-gray-400">{m.acronym}</p>}
              </div>
              <div className="flex gap-2 text-sm">
                <button onClick={() => startEditMinistry(m)} className="text-blue-600 hover:underline">Edit</button>
                <button onClick={() => handleDeleteMinistry(m.id)} className="text-red-600 hover:underline">Delete</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Sources ── */}
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-gray-800">Sources</h2>
        <button
          onClick={() => (showSourceForm ? resetSourceForm() : setShowSourceForm(true))}
          className="bg-green-700 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-green-800"
        >
          {showSourceForm ? 'Cancel' : '+ Add Source'}
        </button>
      </div>

      {showSourceForm && (
        <form onSubmit={handleSourceSubmit} className="bg-white border border-gray-200 rounded-xl p-4 mb-4 space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <input
              placeholder="Source Name *" required
              value={sourceForm.name}
              onChange={(e) => setSourceForm({ ...sourceForm, name: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
            <input
              placeholder="Base URL *" required
              value={sourceForm.base_url}
              onChange={(e) => setSourceForm({ ...sourceForm, base_url: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
            <select
              value={sourceForm.format}
              onChange={(e) => setSourceForm({ ...sourceForm, format: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="html">HTML</option>
              <option value="pdf">PDF</option>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
              <option value="xlsx">XLSX</option>
              <option value="docx">DOCX</option>
              <option value="xml">XML</option>
            </select>
            <select
              value={sourceForm.ministry_id}
              onChange={(e) => setSourceForm({ ...sourceForm, ministry_id: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="">Select Ministry</option>
              {ministries.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
            <input
              type="number" placeholder="Crawl Interval (hours)"
              value={sourceForm.crawl_interval_hours}
              onChange={(e) => setSourceForm({ ...sourceForm, crawl_interval_hours: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
            <input
              type="number" placeholder="Max Depth"
              value={sourceForm.max_depth}
              onChange={(e) => setSourceForm({ ...sourceForm, max_depth: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
            <input
              type="number" step="0.1" placeholder="Rate Limit (req/sec)"
              value={sourceForm.rate_limit_rps}
              onChange={(e) => setSourceForm({ ...sourceForm, rate_limit_rps: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <button
            type="submit" disabled={savingSource}
            className="bg-green-700 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-green-800 disabled:opacity-50"
          >
            {savingSource ? 'Saving...' : editingSourceId ? 'Update Source' : 'Create Source'}
          </button>
        </form>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Format</th>
              <th className="px-4 py-2">Interval</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{s.name}</td>
                <td className="px-4 py-2">{s.format}</td>
                <td className="px-4 py-2">{s.crawl_interval_hours}h</td>
                <td className="px-4 py-2 flex gap-3">
                  <button onClick={() => startEditSource(s)} className="text-blue-600 hover:underline">Edit</button>
                  <button onClick={() => handleDeleteSource(s.id)} className="text-red-600 hover:underline">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}