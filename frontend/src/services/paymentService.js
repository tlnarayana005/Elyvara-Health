import api from './api';

const paymentService = {
  createPayment: (bookingId) =>
    api.post('/payments/', { booking_id: bookingId }),
};

export default paymentService;
