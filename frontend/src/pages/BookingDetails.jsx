import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import bookingService from '../services/bookingService';
import paymentService from '../services/paymentService';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';

function BookingDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(location.state?.justCreated ? 'Booking created successfully!' : '');
  const [showCancelModal, setShowCancelModal] = useState(false);

  const fetchBooking = () => {
    bookingService.getBooking(id)
      .then((res) => setBooking(res.data))
      .catch((err) => setError(err.response?.data?.error || 'Failed to load booking'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchBooking(); }, [id]);

  const handlePayment = async () => {
    setActionLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await paymentService.createPayment(booking.id);
      if (res.data.status === 'SUCCESS') {
        setSuccess('Payment successful! Booking confirmed.');
      } else {
        setError('Payment failed. Please try again.');
      }
      fetchBooking();
    } catch (err) {
      setError(err.response?.data?.error || 'Payment failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    setShowCancelModal(false);
    setActionLoading(true);
    setError('');
    setSuccess('');
    try {
      await bookingService.cancelBooking(booking.id);
      setSuccess('Booking cancelled.');
      fetchBooking();
    } catch (err) {
      setError(err.response?.data?.error || 'Cancellation failed');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading booking..." />;
  if (!booking && error) return <div className="container py-4"><div className="alert alert-danger">{error}</div></div>;

  const canPay = booking.status === 'PENDING';
  const canCancel = ['PENDING', 'CONFIRMED', 'FAILED'].includes(booking.status);

  return (
    <div className="container py-4" style={{ maxWidth: 650 }}>
      <button className="btn btn-sm btn-outline-secondary mb-3" onClick={() => navigate('/bookings')}>
        <i className="bi bi-arrow-left me-1"></i>My Bookings
      </button>

      {success && <div className="alert alert-success">{success}</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card shadow-sm border-0">
        <div className="card-header bg-white d-flex justify-content-between align-items-center py-3">
          <h5 className="mb-0">Booking #{booking.id}</h5>
          <StatusBadge status={booking.status} />
        </div>
        <div className="card-body">
          <div className="row g-3">
            <div className="col-sm-6">
              <small className="text-muted d-block">Centre</small>
              <strong>{booking.centre_name}</strong>
            </div>
            <div className="col-sm-6">
              <small className="text-muted d-block">Test</small>
              <strong>{booking.test_name}</strong>
            </div>
            <div className="col-sm-6">
              <small className="text-muted d-block">Appointment</small>
              <strong>{new Date(booking.appointment_datetime).toLocaleString()}</strong>
            </div>
            <div className="col-sm-6">
              <small className="text-muted d-block">Amount</small>
              <strong className="text-success fs-5">Rs. {booking.amount}</strong>
            </div>
            <div className="col-12">
              <small className="text-muted d-block">Booked On</small>
              {new Date(booking.created_at).toLocaleString()}
            </div>
          </div>
        </div>
        <div className="card-footer bg-white d-flex gap-2 py-3">
          {canPay && (
            <button className="btn btn-success" onClick={handlePayment} disabled={actionLoading}>
              {actionLoading ? 'Processing...' : <><i className="bi bi-credit-card me-1"></i>Pay Now</>}
            </button>
          )}
          {canCancel && (
            <button className="btn btn-outline-danger" onClick={() => setShowCancelModal(true)} disabled={actionLoading}>
              <i className="bi bi-x-circle me-1"></i>Cancel
            </button>
          )}
        </div>
      </div>

      {/* Cancel Confirmation Modal */}
      {showCancelModal && (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Confirm Cancellation</h5>
                <button className="btn-close" onClick={() => setShowCancelModal(false)}></button>
              </div>
              <div className="modal-body">
                Are you sure you want to cancel <strong>Booking #{booking.id}</strong>?
                This action cannot be undone.
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowCancelModal(false)}>Keep Booking</button>
                <button className="btn btn-danger" onClick={handleCancel}>Yes, Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BookingDetails;
