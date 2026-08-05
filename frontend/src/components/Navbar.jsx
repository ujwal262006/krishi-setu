import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { farmer, logout, isLoggedIn } = useAuth()
  const location = useLocation()

  if (!isLoggedIn) return null

  const farmerLinks = [
    { to: '/browse', label: 'Browse' },
    { to: '/eligibility', label: 'Eligibility' },
    { to: '/assistant', label: 'Assistant' },
    { to: '/eligibility-history', label: 'History' },
  ]

  const linkClass = (path) =>
    `text-sm font-medium ${location.pathname === path ? 'text-green-700' : 'text-gray-500'}`

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-10">
      <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3 flex-wrap gap-y-2">
        <span className="font-bold text-green-800 text-lg">Krishi Setu 🌾</span>
        <div className="flex gap-4 items-center flex-wrap">
          {farmerLinks.map((l) => (
            <Link key={l.to} to={l.to} className={linkClass(l.to)}>
              {l.label}
            </Link>
          ))}
          <span className="text-sm text-gray-300 hidden sm:inline">|</span>
          <Link to="/profile" className={linkClass('/profile') + ' hidden sm:inline'}>
            {farmer?.name}
          </Link>
          <button onClick={logout} className="text-sm text-red-600 font-medium">
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}