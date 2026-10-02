import api from './api';

const centreService = {
  getCentres: () => api.get('/centres/'),
  getCentre: (id) => api.get(`/centres/${id}`),
  getCentreTests: (id) => api.get(`/centres/${id}/tests`),
  createCentre: (data) => api.post('/centres/', data),
  updateCentre: (id, data) => api.patch(`/centres/${id}`, data),
};

export default centreService;
