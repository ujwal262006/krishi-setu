import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMyProfile, updateMyProfile, deleteMyAccount } from '../api/auth'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const [form, setForm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    getMyProfile()
      .then((res) => {
        const d = res.data
        setForm({
          name: d.name || '',
          state: d.state || '',
          district: d.district || '',
          land_holding_acres: d.land_holding_acres ?? '',
          caste: d.caste || '',
          annual_income: d.annual_income ?? '',
          age: d.age ?? '',
          gender: d.gender || '',
          is_bpl: d.is_bpl === null || d.is_bpl === undefined ? '' : String(d.is_bpl),
          has_kisan_credit_card:
            d.has_kisan_credit_card === null || d.has_kisan_credit_card === undefined
              ? ''
              : String(d.has_kisan_credit_card),
          primary_crop: d.primary_crop || '',
          irrigation_type: d.irrigation_type || '',
        })
      })
      .catch(() => setError('Could not load profile.'))
      .finally(() => setLoading(false))
  }, [])

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const payload = {
        name: form.name,
        state: form.state || null,
        district: form.district || null,
        land_holding_acres: form.land_holding_acres ? parseFloat(form.land_holding_acres) : null,
        caste: form.caste || null,
        annual_income: form.annual_income ? parseInt(form.annual_income) : null,
        age: form.age ? parseInt(form.age) : null,
        gender: form.gender || null,
        is_bpl: form.is_bpl === '' ? null : form.is_bpl === 'true',
        has_kisan_credit_card: form.has_kisan_credit_card === '' ? null : form.has_kisan_credit_card === 'true',
        primary_crop: form.primary_crop || null,
        irrigation_type: form.irrigation_type || null,
      }
      await updateMyProfile(payload)
      setSuccess('Profile updated successfully.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteAccount = async () => {
    const confirmed = confirm(
      'Are you sure you want to delete your account? This will deactivate your profile and you will be logged out. This cannot be undone.'
    )
    if (!confirmed) return

    setDeleting(true)
    try {
      await deleteMyAccount()
      logout()
      navigate('/login')
    } catch (err) {
      setError('Failed to delete account. Please try again.')
      setDeleting(false)
    }
  }

  if (loading) return <div className="max-w-2xl mx-auto p-4 text-gray-500">Loading...</div>
  if (!form) return <div className="max-w-2xl mx-auto p-4 text-red-600">{error}</div>

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold text-green-800 mb-2">My Profile</h1>
      <p className="text-sm text-gray-500 mb-6">
        Keep this complete and accurate for correct eligibility results.
      </p>

      {error && <div className="bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">{error}</div>}
      {success && <div className="bg-green-50 text-green-700 text-sm rounded-lg px-3 py-2 mb-4">{success}</div>}

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm p-6 space-y-3">
        <input name="name" placeholder="Full Name *" value={form.name} onChange={handleChange} required
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />

        <div className="grid grid-cols-2 gap-3">
          <input name="state" placeholder="State" value={form.state} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <input name="district" placeholder="District" value={form.district} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <input name="age" type="number" placeholder="Age" value={form.age} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <select name="gender" value={form.gender} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500">
            <option value="">Gender</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <input name="land_holding_acres" type="number" step="0.1" placeholder="Land (acres)"
            value={form.land_holding_acres} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <input name="annual_income" type="number" placeholder="Annual Income (₹)"
            value={form.annual_income} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />
        </div>

        <select name="caste" value={form.caste} onChange={handleChange}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500">
          <option value="">Category (General/SC/ST/OBC)</option>
          <option value="general">General</option>
          <option value="sc">SC</option>
          <option value="st">ST</option>
          <option value="obc">OBC</option>
        </select>

        <div className="grid grid-cols-2 gap-3">
          <select name="is_bpl" value={form.is_bpl} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500">
            <option value="">BPL Status?</option>
            <option value="true">Yes, BPL</option>
            <option value="false">No, not BPL</option>
          </select>
          <select name="has_kisan_credit_card" value={form.has_kisan_credit_card} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500">
            <option value="">Kisan Credit Card?</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <input name="primary_crop" placeholder="Primary Crop" value={form.primary_crop} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <select name="irrigation_type" value={form.irrigation_type} onChange={handleChange}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500">
            <option value="">Irrigation Type</option>
            <option value="canal">Canal</option>
            <option value="borewell">Borewell</option>
            <option value="rainfed">Rainfed</option>
            <option value="drip">Drip</option>
            <option value="other">Other</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-green-700 text-white font-semibold py-2 rounded-lg mt-2 hover:bg-green-800 transition disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </form>

      <div className="mt-8 border-t border-gray-200 pt-6">
        <h2 className="text-sm font-semibold text-red-700 mb-2">Danger Zone</h2>
        <p className="text-xs text-gray-500 mb-3">
          Deleting your account will deactivate your profile permanently.
        </p>
        <button
          onClick={handleDeleteAccount}
          disabled={deleting}
          className="text-sm text-red-600 border border-red-200 rounded-lg px-4 py-2 hover:bg-red-50 transition disabled:opacity-50"
        >
          {deleting ? 'Deleting...' : 'Delete My Account'}
        </button>
      </div>
    </div>
  )
}