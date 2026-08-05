import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AdminNavbar() {
  const { isAdmin, adminLogout } = useAuth()
  const location = useLocation()

  const adminLinks = [
    { to: '/admin', label: 'Admin' },
    { to: '/crawler', label: 'Crawler' },
    { to: '/master', label: 'Master' },
  ]

  const linkClass = (path) =>
    `text-sm font-medium ${location.pathname === path ? 'text-white' : 'text-gray-400'}`

  return (
    <nav className="bg-gray-900 shadow-sm sticky top-0 z-10">
      <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3 flex-wrap gap-y-2">
        <span className="font-bold text-gray-100 text-lg">Krishi Setu — Admin ⚙️</span>
        {isAdmin && (
          <div className="flex gap-4 items-center flex-wrap">
            {adminLinks.map((l) => (
              <Link key={l.to} to={l.to} className={linkClass(l.to)}>
                {l.label}
              </Link>
            ))}
            <span className="text-sm text-gray-600">|</span>
            <button onClick={adminLogout} className="text-sm text-red-400 font-medium">
              Admin Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}