import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AdminLogin() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { adminLogin } = useAuth()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (adminLogin(password)) {
      navigate('/admin')
    } else {
      setError('Incorrect admin password.')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-md p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-gray-800 mb-2 text-center">Admin Access</h1>
        <p className="text-sm text-gray-500 text-center mb-6">Internal use only</p>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">{error}</div>
        )}

        <label className="block text-sm font-medium text-gray-700 mb-1">Admin Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-6 focus:outline-none focus:ring-2 focus:ring-gray-700"
        />

        <button
          type="submit"
          className="w-full bg-gray-800 text-white font-semibold py-2 rounded-lg hover:bg-gray-900 transition"
        >
          Enter
        </button>

        <p className="text-sm text-center text-gray-500 mt-6">
          <Link to="/login" className="hover:text-gray-700 underline">
            ← Back to Farmer Login
          </Link>
        </p>
      </form>
    </div>
  )
}