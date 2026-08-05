import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { loginFarmer } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import { normalizePhone } from '../utils/phone'

export default function Login() {
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await loginFarmer({ phone: normalizePhone(phone), password })
      login(res.data.access_token, {
        id: res.data.farmer_id,
        name: res.data.name,
      })
      navigate('/browse')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your phone/password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-green-50 flex items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-md p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-green-800 mb-6 text-center">Krishi Setu Login</h1>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">{error}</div>
        )}

        <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
        <input
          type="text"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          required
          className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-green-500"
        />

        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-6 focus:outline-none focus:ring-2 focus:ring-green-500"
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-green-700 text-white font-semibold py-2 rounded-lg hover:bg-green-800 transition disabled:opacity-50"
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>

        <p className="text-sm text-center text-gray-600 mt-4">
          New farmer?{' '}
          <Link to="/register" className="text-green-700 font-medium">
            Register here
          </Link>
        </p>

        <p className="text-xs text-center text-gray-400 mt-6">
          <Link to="/admin-login" className="hover:text-gray-600 underline">
            Admin Login
          </Link>
        </p>
      </form>
    </div>
  )
}