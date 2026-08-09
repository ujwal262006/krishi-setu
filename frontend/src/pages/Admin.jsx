import { useState, useEffect } from 'react'
import {
  getAdminStats,
  listSchemesAdmin,
  createSchemeAdmin,
  updateSchemeAdmin,
  deleteSchemeAdmin,
  toggleSchemeActive,
  listMinistriesAdmin,
  listFarmersAdmin,
  listSearchLogsAdmin,
} from '../api/admin'

const emptyForm = {
  name: '',
  slug: '',
  name_hindi: '',
  description: '',
  application_url: '',
  ministry_id: '',
  search_synonyms: '',
  eligibility_criteria: '',
  benefits: '',
}

export default function Admin() {
  const [stats, setStats] = useState(null)
  const [schemes, setSchemes] = useState([])
  const [ministries, setMinistries] = useState([])
  const [farmers, setFarmers] = useState([])
  const [searchLogs, setSearchLogs] = useState([])
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  const loadAll = async () => {
    try {
      const [statsRes, schemesRes, ministriesRes, farmersRes, logsRes] = await Promise.all([
        getAdminStats(),
        listSchemesAdmin({ limit: 100 }),
        listMinistriesAdmin(),
        listFarmersAdmin({ limit: 20 }),
        listSearchLogsAdmin({ limit: 20 }),
      ])
      setStats(statsRes.data)
      setSchemes(schemesRes.data)
      setMinistries(ministriesRes.data)
      setFarmers(farmersRes.data.farmers)
      setSearchLogs(logsRes.data.logs)
    } catch (err) {
      setError('Could not load admin data.')
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const resetForm = () => {
    setForm(emptyForm)
    setEditingId(null)
    setShowForm(false)
  }

  const startEdit = (scheme) => {
    setForm({
      name: scheme.name || '',
      slug: scheme.slug || '',
      name_hindi: scheme.name_hindi || '',
      description: scheme.description || '',
      application_url: scheme.application_url || '',
      ministry_id: scheme.ministry_id || '',
      search_synonyms: (scheme.search_synonyms || []).join(', '),
      eligibility_criteria: scheme.eligibility_criteria
        ? JSON.stringify(scheme.eligibility_criteria, null, 2)
        : '',
      benefits: scheme.benefits ? JSON.stringify(scheme.benefits, null, 2) : '',
    })
    setEditingId(scheme.id)
    setShowForm(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    let eligibilityCriteria = {}
    let benefits = {}

    if (form.eligibility_criteria.trim()) {
      try {
        eligibilityCriteria = JSON.parse(form.eligibility_criteria)
      } catch {
        setError('Eligibility Criteria must be valid JSON.')
        setSaving(false)
        return
      }
    }

    if (form.benefits.trim()) {
      try {
        benefits = JSON.parse(form.benefits)
      } catch {
        setError('Benefits must be valid JSON.')
        setSaving(false)
        return
      }
    }

    try {
      const payload = {
        name: form.name,
        name_hindi: form.name_hindi || null,
        description: form.description || null,
        application_url: form.application_url || null,
        ministry_id: form.ministry_id ? parseInt(form.ministry_id) : null,
        search_synonyms: form.search_synonyms
          ? form.search_synonyms.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
        eligibility_criteria: eligibilityCriteria,
        benefits: benefits,
      }

      if (editingId) {
        await updateSchemeAdmin(editingId, payload)
      } else {
        await createSchemeAdmin({ ...payload, slug: form.slug })
      }

      resetForm()
      await loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save scheme.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this scheme? This cannot be undone.')) return
    try {
      await deleteSchemeAdmin(id)
      await loadAll()
    } catch (err) {
      setError('Failed to delete scheme (it may have linked eligibility records).')
    }
  }

  const handleToggle = async (id) => {
    try {
      await toggleSchemeActive(id)
      await loadAll()
    } catch (err) {
      setError('Failed to toggle scheme status.')
    }
  }

  if (!stats) return <div className="max-w-5xl mx-auto p-4 text-gray-500">Loading...</div>

  const cards = [
    { label: 'Total Schemes', value: stats.schemes.total, sub: `${stats.schemes.active} active` },
    { label: 'Total Farmers', value: stats.farmers.total, sub: `${stats.farmers.active} active` },
    { label: 'Sources', value: stats.crawler.total_sources, sub: `${stats.crawler.running_jobs} jobs running` },
    { label: 'Searches', value: stats.usage.total_searches, sub: `${stats.usage.total_eligibility_checks} eligibility checks` },
  ]

  return (
    <div className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold text-green-800 mb-6">Admin Dashboard</h1>

      <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {cards.map((c) => (
          <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-sm text-gray-500">{c.label}</p>
            <p className="text-2xl font-bold text-green-800">{c.value}</p>
            <p className="text-xs text-gray-400 mt-1">{c.sub}</p>
          </div>
        ))}
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {/* ── Schemes ── */}
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-gray-800">Schemes</h2>
        <button
          onClick={() => (showForm ? resetForm() : setShowForm(true))}
          className="bg-green-700 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-green-800"
        >
          {showForm ? 'Cancel' : '+ Add Scheme'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-4 mb-6 space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <input name="name" placeholder="Scheme Name *" value={form.name} onChange={handleChange} required
              className="border border-gray-300 rounded-lg px-3 py-2" />
            {!editingId && (
              <input name="slug" placeholder="Slug * (e.g. pm-kisan)" value={form.slug} onChange={handleChange} required
                className="border border-gray-300 rounded-lg px-3 py-2" />
            )}
            <input name="name_hindi" placeholder="Name (Hindi)" value={form.name_hindi} onChange={handleChange}
              className="border border-gray-300 rounded-lg px-3 py-2" />
            <select name="ministry_id" value={form.ministry_id} onChange={handleChange}
              className="border border-gray-300 rounded-lg px-3 py-2">
              <option value="">Select Ministry</option>
              {ministries.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
            <input name="application_url" placeholder="Application URL" value={form.application_url} onChange={handleChange}
              className="border border-gray-300 rounded-lg px-3 py-2 sm:col-span-2" />
            <input name="search_synonyms" placeholder="Synonyms, comma separated" value={form.search_synonyms} onChange={handleChange}
              className="border border-gray-300 rounded-lg px-3 py-2 sm:col-span-2" />
          </div>

          <textarea name="description" placeholder="Description" value={form.description} onChange={handleChange} rows={3}
            className="w-full border border-gray-300 rounded-lg px-3 py-2" />

          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">
              Eligibility Criteria (JSON) — e.g. {`{"land_holding": {"max_acres": 5}, "age": {"min": 18}}`}
            </label>
            <textarea
              name="eligibility_criteria"
              placeholder='{"land_holding": {"max_acres": 5}}'
              value={form.eligibility_criteria}
              onChange={handleChange}
              rows={4}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 font-mono text-xs"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">
              Benefits (JSON) — e.g. {`{"subsidy": "40%", "max_amount": 50000}`}
            </label>
            <textarea
              name="benefits"
              placeholder='{"subsidy": "40%"}'
              value={form.benefits}
              onChange={handleChange}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 font-mono text-xs"
            />
          </div>

          <button type="submit" disabled={saving}
            className="bg-green-700 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-green-800 disabled:opacity-50">
            {saving ? 'Saving...' : editingId ? 'Update Scheme' : 'Create Scheme'}
          </button>
        </form>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto mb-8">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr><th className="px-4 py-2">Name</th><th className="px-4 py-2">Status</th><th className="px-4 py-2"></th></tr>
          </thead>
          <tbody>
            {schemes.map((s) => (
              <tr key={s.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{s.name}</td>
                <td className="px-4 py-2">
                  <span className={s.is_active ? 'text-green-700' : 'text-gray-400'}>
                    {s.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-2 flex gap-3">
                  <button onClick={() => startEdit(s)} className="text-blue-600 hover:underline">Edit</button>
                  <button onClick={() => handleToggle(s.id)} className="text-amber-600 hover:underline">
                    {s.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                  <button onClick={() => handleDelete(s.id)} className="text-red-600 hover:underline">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Farmers ── */}
      <h2 className="text-lg font-semibold text-gray-800 mb-3">Registered Farmers</h2>
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto mb-8">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Phone</th>
              <th className="px-4 py-2">State</th>
              <th className="px-4 py-2">District</th>
              <th className="px-4 py-2">Land (acres)</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {farmers.map((f) => (
              <tr key={f.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{f.name}</td>
                <td className="px-4 py-2">{f.phone || '—'}</td>
                <td className="px-4 py-2">{f.state || '—'}</td>
                <td className="px-4 py-2">{f.district || '—'}</td>
                <td className="px-4 py-2">{f.land_holding_acres ?? '—'}</td>
                <td className="px-4 py-2">
                  <span className={f.is_active ? 'text-green-700' : 'text-gray-400'}>
                    {f.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Search Logs ── */}
      <h2 className="text-lg font-semibold text-gray-800 mb-3">Recent Search Logs</h2>
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto mb-8">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-2">Query</th>
              <th className="px-4 py-2">Results</th>
              <th className="px-4 py-2">Response Time</th>
              <th className="px-4 py-2">Date</th>
            </tr>
          </thead>
          <tbody>
            {searchLogs.map((l) => (
              <tr key={l.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{l.query_raw}</td>
                <td className="px-4 py-2">{l.results_count}</td>
                <td className="px-4 py-2">{l.response_time_ms} ms</td>
                <td className="px-4 py-2">{new Date(l.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Crawl Jobs ── */}
      <h2 className="text-lg font-semibold text-gray-800 mb-3">Recent Crawl Jobs</h2>
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-2">ID</th>
              <th className="px-4 py-2">Source</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">URLs Crawled</th>
              <th className="px-4 py-2">Schemes Upserted</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_crawl_jobs.map((j) => (
              <tr key={j.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{j.id}</td>
                <td className="px-4 py-2">{j.source_id}</td>
                <td className="px-4 py-2">{j.status}</td>
                <td className="px-4 py-2">{j.urls_crawled}</td>
                <td className="px-4 py-2">{j.schemes_upserted}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}