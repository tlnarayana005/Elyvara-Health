import api from './api';

const bookingService = {
  createBooking: (centreTestId, appointmentDatetime) =>
    api.post('/bookings/', {
      centre_test_id: centreTestId,
      appointment_datetime: appointmentDatetime,
    }),

  getBookings: () => api.get('/bookings/'),

  getBooking: (id) => api.get(`/bookings/${id}`),

  cancelBooking: (id) => api.post(`/bookings/${id}/cancel`),
};

export default bookingService;
