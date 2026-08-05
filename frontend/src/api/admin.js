import api from './axiosInstance'

// Stats
export const getAdminStats = () => api.get('/admin/stats')

// Schemes
export const listSchemesAdmin = (params) => api.get('/admin/schemes', { params })
export const createSchemeAdmin = (data) => api.post('/admin/schemes', data)
export const updateSchemeAdmin = (id, data) => api.patch(`/admin/schemes/${id}`, data)
export const deleteSchemeAdmin = (id) => api.delete(`/admin/schemes/${id}`)
export const toggleSchemeActive = (id) => api.patch(`/admin/schemes/${id}/toggle`)

// Sources
export const listSourcesAdmin = () => api.get('/admin/sources')
export const createSourceAdmin = (data) => api.post('/admin/sources', data)
export const updateSourceAdmin = (id, data) => api.patch(`/admin/sources/${id}`, data)
export const deleteSourceAdmin = (id) => api.delete(`/admin/sources/${id}`)

// Ministries (admin - list + create)
export const listMinistriesAdmin = () => api.get('/admin/ministries')
export const createMinistryAdmin = (data) => api.post('/admin/ministries', data)

// Ministries (dedicated router - update + delete)
export const updateMinistry = (id, data) => api.patch(`/ministries/${id}`, data)
export const deleteMinistry = (id) => api.delete(`/ministries/${id}`)

// Farmers / Crawl jobs
export const listFarmersAdmin = (params) => api.get('/admin/farmers', { params })
export const listCrawlJobsAdmin = (params) => api.get('/admin/crawl-jobs', { params })
export const triggerCrawlAdmin = (sourceId) => api.post(`/admin/crawl-jobs/trigger/${sourceId}`)

// Search logs
export const listSearchLogsAdmin = (params) => api.get('/admin/search-logs', { params })