import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Browse from './pages/Browse'
import Eligibility from './pages/Eligibility'
import Assistant from './pages/Assistant'
import Profile from './pages/Profile'
import SchemeDetail from './pages/SchemeDetail'
import EligibilityHistory from './pages/EligibilityHistory'
import Admin from './pages/Admin'
import Crawler from './pages/Crawler'
import Master from './pages/Master'
import AdminLogin from './pages/AdminLogin'
import NotFound from './pages/NotFound'
import Navbar from './components/Navbar'
import AdminNavbar from './components/AdminNavbar'
import { useAuth } from './context/AuthContext'

function ProtectedRoute({ children }) {
  const { isLoggedIn } = useAuth()
  return isLoggedIn ? children : <Navigate to="/login" />
}

function PublicOnlyRoute({ children }) {
  const { isLoggedIn } = useAuth()
  return isLoggedIn ? <Navigate to="/browse" /> : children
}

function AdminRoute({ children }) {
  const { isAdmin } = useAuth()
  return isAdmin ? children : <Navigate to="/admin-login" />
}

function App() {
  const location = useLocation()
  const isAdminSection =
    location.pathname.startsWith('/admin') ||
    location.pathname.startsWith('/crawler') ||
    location.pathname.startsWith('/master')

  return (
    <div className={isAdminSection ? 'min-h-screen bg-gray-100' : 'min-h-screen bg-green-50'}>
      {isAdminSection ? <AdminNavbar /> : <Navbar />}
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
        <Route path="/register" element={<PublicOnlyRoute><Register /></PublicOnlyRoute>} />
        <Route path="/browse" element={<ProtectedRoute><Browse /></ProtectedRoute>} />
        <Route path="/schemes/:id" element={<ProtectedRoute><SchemeDetail /></ProtectedRoute>} />
        <Route path="/eligibility" element={<ProtectedRoute><Eligibility /></ProtectedRoute>} />
        <Route path="/eligibility-history" element={<ProtectedRoute><EligibilityHistory /></ProtectedRoute>} />
        <Route path="/assistant" element={<ProtectedRoute><Assistant /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/admin-login" element={<AdminLogin />} />
        <Route path="/admin" element={<AdminRoute><Admin /></AdminRoute>} />
        <Route path="/crawler" element={<AdminRoute><Crawler /></AdminRoute>} />
        <Route path="/master" element={<AdminRoute><Master /></AdminRoute>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  )
}

export default App