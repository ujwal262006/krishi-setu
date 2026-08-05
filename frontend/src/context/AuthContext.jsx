import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [farmer, setFarmer] = useState(() => {
    const saved = localStorage.getItem('krishi_farmer')
    return saved ? JSON.parse(saved) : null
  })

  const [isAdmin, setIsAdmin] = useState(() => {
    return localStorage.getItem('krishi_is_admin') === 'true'
  })

  const login = (token, farmerData) => {
    localStorage.setItem('krishi_token', token)
    localStorage.setItem('krishi_farmer', JSON.stringify(farmerData))
    setFarmer(farmerData)
  }

  const logout = () => {
    localStorage.removeItem('krishi_token')
    localStorage.removeItem('krishi_farmer')
    setFarmer(null)
  }

  const adminLogin = (password) => {
    if (password === import.meta.env.VITE_ADMIN_PASSWORD) {
      localStorage.setItem('krishi_is_admin', 'true')
      setIsAdmin(true)
      return true
    }
    return false
  }

  const adminLogout = () => {
    localStorage.removeItem('krishi_is_admin')
    setIsAdmin(false)
  }

  return (
    <AuthContext.Provider
      value={{ farmer, login, logout, isLoggedIn: !!farmer, isAdmin, adminLogin, adminLogout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}