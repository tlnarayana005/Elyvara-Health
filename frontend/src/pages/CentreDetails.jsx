import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import centreService from '../services/centreService';
import LoadingSpinner from '../components/LoadingSpinner';

function CentreDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [centre, setCentre] = useState(null);
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      centreService.getCentre(id),
      centreService.getCentreTests(id),
    ])
      .then(([centreRes, testsRes]) => {
        setCentre(centreRes.data);
        setTests(testsRes.data);
      })
      .catch((err) => setError(err.response?.data?.error || 'Failed to load centre'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleBook = (centreTest) => {
    navigate('/booking', { state: { centreTest, centre } });
  };

  if (loading) return <LoadingSpinner message="Loading centre details..." />;
  if (error) return <div className="container py-4"><div className="alert alert-danger">{error}</div></div>;

  return (
    <div className="container py-4">
      <button className="btn btn-sm btn-outline-secondary mb-3" onClick={() => navigate('/centres')}>
        <i className="bi bi-arrow-left me-1"></i>Back to Centres
      </button>
      <div className="card shadow-sm border-0 mb-4">
        <div className="card-body">
          <h3><i className="bi bi-building me-2 text-primary"></i>{centre.name}</h3>
          <p className="text-muted mb-0"><i className="bi bi-geo-alt me-1"></i>{centre.location}</p>
        </div>
      </div>

      <h4 className="mb-3">Available Tests</h4>
      {tests.length === 0 ? (
        <div className="alert alert-info">No tests available at this centre.</div>
      ) : (
        <div className="row g-3">
          {tests.map((t) => (
            <div className="col-md-6" key={t.id}>
              <div className="card h-100 shadow-sm border-0">
                <div className="card-body d-flex justify-content-between align-items-center">
                  <div>
                    <h6 className="mb-1">{t.test_name}</h6>
                    <span className="text-success fw-bold fs-5">Rs. {t.price}</span>
                  </div>
                  <button className="btn btn-primary" onClick={() => handleBook(t)}>
                    Book
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CentreDetails;
