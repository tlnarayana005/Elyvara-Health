import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import bookingService from '../services/bookingService';

function Booking() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [date, setDate] = useState('');
  const [time, setTime] = useState('09:00');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!state?.centreTest || !state?.centre) {
    return (
      <div className="container py-4">
        <div className="alert alert-warning">
          No test selected. <a href="/centres">Browse centres</a> to pick a test.
        </div>
      </div>
    );
  }

  const { centreTest, centre } = state;

  // Minimum date = tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split('T')[0];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const appointmentDatetime = `${date}T${time}:00`;
      const res = await bookingService.createBooking(centreTest.id, appointmentDatetime);
      navigate(`/bookings/${res.data.id}`, { state: { justCreated: true } });
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create booking');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-4" style={{ maxWidth: 600 }}>
      <h3 className="mb-4">
        <i className="bi bi-calendar-plus me-2 text-primary"></i>Book Appointment
      </h3>

      {/* Summary Card */}
      <div className="card shadow-sm border-0 mb-4">
        <div className="card-body">
          <div className="row">
            <div className="col-6">
              <small className="text-muted">Centre</small>
              <p className="fw-bold mb-2">{centre.name}</p>
            </div>
            <div className="col-6">
              <small className="text-muted">Location</small>
              <p className="mb-2">{centre.location}</p>
            </div>
            <div className="col-6">
              <small className="text-muted">Test</small>
              <p className="fw-bold mb-2">{centreTest.test_name}</p>
            </div>
            <div className="col-6">
              <small className="text-muted">Price</small>
              <p className="fw-bold text-success fs-5 mb-0">Rs. {centreTest.price}</p>
            </div>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label">Appointment Date</label>
          <input
            type="date"
            className="form-control"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            min={minDate}
            required
          />
        </div>
        <div className="mb-4">
          <label className="form-label">Preferred Time</label>
          <select className="form-select" value={time} onChange={(e) => setTime(e.target.value)}>
            {['09:00','09:30','10:00','10:30','11:00','11:30','12:00','14:00','14:30','15:00','15:30','16:00','16:30'].map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <button className="btn btn-primary w-100 btn-lg" disabled={loading}>
          {loading ? 'Creating Booking...' : 'Confirm Booking'}
        </button>
      </form>
    </div>
  );
}

export default Booking;
