import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import centreService from '../services/centreService';
import LoadingSpinner from '../components/LoadingSpinner';

function Centres() {
  const [centres, setCentres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    centreService.getCentres()
      .then((res) => setCentres(res.data))
      .catch((err) => setError(err.response?.data?.error || 'Failed to load centres'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading centres..." />;

  return (
    <div className="container py-4">
      <h2 className="mb-4">
        <i className="bi bi-hospital me-2 text-primary"></i>Diagnostic Centres
      </h2>
      {error && <div className="alert alert-danger">{error}</div>}
      {centres.length === 0 && !error && (
        <div className="alert alert-info">No centres available.</div>
      )}
      <div className="row g-4">
        {centres.map((c) => (
          <div className="col-md-6 col-lg-4" key={c.id}>
            <div className="card h-100 shadow-sm border-0">
              <div className="card-body">
                <h5 className="card-title">
                  <i className="bi bi-building me-2 text-primary"></i>{c.name}
                </h5>
                <p className="card-text text-muted">
                  <i className="bi bi-geo-alt me-1"></i>{c.location}
                </p>
              </div>
              <div className="card-footer bg-transparent border-0 pb-3">
                <Link to={`/centres/${c.id}`} className="btn btn-outline-primary w-100">
                  View Tests & Book
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Centres;
