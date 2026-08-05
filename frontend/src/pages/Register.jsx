import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { registerFarmer } from '../api/auth'
import { normalizePhone } from '../utils/phone'

export default function Register() {
  const [form, setForm] = useState({
    name: '', phone: '', password: '', state: '', district: '',
    land_holding_acres: '', caste: '', annual_income: '', age: '',
    gender: '', is_bpl: '', has_kisan_credit_card: '', primary_crop: '', irrigation_type: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        ...form,
        phone: normalizePhone(form.phone),
        land_holding_acres: form.land_holding_acres ? parseFloat(form.land_holding_acres) : null,
        annual_income: form.annual_income ? parseInt(form.annual_income) : null,
        age: form.age ? parseInt(form.age) : null,
        is_bpl: form.is_bpl === '' ? null : form.is_bpl === 'true',
        has_kisan_credit_card: form.has_kisan_credit_card === '' ? null : form.has_kisan_credit_card === 'true',
        caste: form.caste || null,
        gender: form.gender || null,
        irrigation_type: form.irrigation_type || null,
      }
      await registerFarmer(payload)
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-green-50 flex items-center justify-center px-4 py-8">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-md p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-green-800 mb-2 text-center">Farmer Registration</h1>
        <p className="text-xs text-gray-500 text-center mb-6">
          Fill this completely for accurate eligibility checks
        </p>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">{error}</div>
        )}

        <div className="space-y-3">
          <input name="name" placeholder="Full Name *" value={form.name} onChange={handleChange} required
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />

          <input name="phone" placeholder="Phone Number" value={form.phone} onChange={handleChange}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />

          <input name="password" type="password" placeholder="Password *" value={form.password} onChange={handleChange} required
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
            <input name="land_holding_acres" type="number" step="0.1" placeholder="Land (acres)" value={form.land_holding_acres} onChange={handleChange}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500" />
            <input name="annual_income" type="number" placeholder="Annual Income (₹)" value={form.annual_income} onChange={handleChange}
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
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-green-700 text-white font-semibold py-2 rounded-lg mt-6 hover:bg-green-800 transition disabled:opacity-50"
        >
          {loading ? 'Registering...' : 'Register'}
        </button>

        <p className="text-sm text-center text-gray-600 mt-4">
          Already registered?{' '}
          <Link to="/login" className="text-green-700 font-medium">
            Login
          </Link>
        </p>
      </form>
    </div>
  )
}