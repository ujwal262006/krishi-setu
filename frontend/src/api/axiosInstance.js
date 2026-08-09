import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

// Har request ke saath token attach karo (agar login hai)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('krishi_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Agar token expire/invalid ho (401), to login page pe bhej do
// Login/Register endpoints ke liye ye redirect skip karo, warna login fail hone pe hi loop ho jata h
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthEndpoint =
      error.config?.url?.includes('/login') || error.config?.url?.includes('/register')

    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('krishi_token')
      localStorage.removeItem('krishi_farmer')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api