import api from './axiosInstance'

export const registerFarmer = (data) => api.post('/farmers/register', data)

export const loginFarmer = (data) => api.post('/farmers/login', data)

export const getMyProfile = () => api.get('/farmers/me')

export const updateMyProfile = (data) => api.patch('/farmers/me', data)

export const deleteMyAccount = () => api.delete('/farmers/me')