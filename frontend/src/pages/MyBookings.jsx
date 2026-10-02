import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import bookingService from '../services/bookingService';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';

function MyBookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    bookingService.getBookings()
      .then((res) => setBookings(res.data))
      .catch((err) => setError(err.response?.data?.error || 'Failed to load bookings'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading your bookings..." />;

  return (
    <div className="container py-4">
      <h2 className="mb-4">
        <i className="bi bi-journal-medical me-2 text-primary"></i>My Bookings
      </h2>
      {error && <div className="alert alert-danger">{error}</div>}
      {bookings.length === 0 && !error && (
        <div className="text-center py-5">
          <i className="bi bi-calendar-x fs-1 text-muted"></i>
          <p className="mt-3 text-muted">You have no bookings yet.</p>
          <Link to="/centres" className="btn btn-primary">Browse Centres</Link>
        </div>
      )}
      <div className="row g-3">
        {bookings.map((b) => (
          <div className="col-md-6 col-lg-4" key={b.id}>
            <div className="card h-100 shadow-sm border-0">
              <div className="card-body">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <h6 className="mb-0">Booking #{b.id}</h6>
                  <StatusBadge status={b.status} />
                </div>
                <p className="mb-1"><strong>{b.test_name}</strong></p>
                <p className="text-muted small mb-1">
                  <i className="bi bi-building me-1"></i>{b.centre_name}
                </p>
                <p className="text-muted small mb-2">
                  <i className="bi bi-calendar me-1"></i>
                  {new Date(b.appointment_datetime).toLocaleString()}
                </p>
                <p className="fw-bold text-success mb-0">Rs. {b.amount}</p>
              </div>
              <div className="card-footer bg-transparent border-0 pb-3">
                <Link to={`/bookings/${b.id}`} className="btn btn-outline-primary btn-sm w-100">
                  View Details
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MyBookings;
