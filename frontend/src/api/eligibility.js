import api from './axiosInstance'

export const checkEligibility = (schemeIds) =>
  api.post('/eligibility/check', schemeIds)

export const getMyEligibilityResults = () => api.get('/eligibility/my-results')