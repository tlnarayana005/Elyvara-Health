import api from './api';

const testService = {
  getTests: () => api.get('/tests/'),
  getTest: (id) => api.get(`/tests/${id}`),
  createTest: (data) => api.post('/tests/', data),
  updateTest: (id, data) => api.patch(`/tests/${id}`, data),
  createCentreTest: (data) => api.post('/tests/centre-tests', data),
};

export default testService;
