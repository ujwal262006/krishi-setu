import api from './axiosInstance'

export const listSchemes = (params) => api.get('/schemes/', { params })

export const searchSchemes = (q, limit = 10, offset = 0) =>
  api.get('/schemes/search', { params: { q, limit, offset } })

export const getScheme = (id) => api.get(`/schemes/${id}`)