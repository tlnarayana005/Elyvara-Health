import { useState, useEffect } from 'react';
import centreService from '../services/centreService';
import testService from '../services/testService';
import LoadingSpinner from '../components/LoadingSpinner';

function Admin() {
  const [centres, setCentres] = useState([]);
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form states
  const [centreName, setCentreName] = useState('');
  const [centreLocation, setCentreLocation] = useState('');
  const [testName, setTestName] = useState('');
  const [testDesc, setTestDesc] = useState('');
  const [ctCentreId, setCtCentreId] = useState('');
  const [ctTestId, setCtTestId] = useState('');
  const [ctPrice, setCtPrice] = useState('');

  const fetchData = async () => {
    try {
      const [cRes, tRes] = await Promise.all([
        centreService.getCentres(),
        testService.getTests(),
      ]);
      setCentres(cRes.data);
      setTests(tRes.data);
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreateCentre = async (e) => {
    e.preventDefault();
    setError(''); setSuccess('');
    try {
      await centreService.createCentre({ name: centreName, location: centreLocation });
      setSuccess('Centre created!');
      setCentreName(''); setCentreLocation('');
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create centre');
    }
  };

  const handleCreateTest = async (e) => {
    e.preventDefault();
    setError(''); setSuccess('');
    try {
      await testService.createTest({ name: testName, description: testDesc });
      setSuccess('Test created!');
      setTestName(''); setTestDesc('');
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create test');
    }
  };

  const handleLinkCentreTest = async (e) => {
    e.preventDefault();
    setError(''); setSuccess('');
    try {
      await testService.createCentreTest({
        centre_id: parseInt(ctCentreId),
        test_id: parseInt(ctTestId),
        price: parseFloat(ctPrice),
      });
      setSuccess('Centre-test linked!');
      setCtCentreId(''); setCtTestId(''); setCtPrice('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to link');
    }
  };

  if (loading) return <LoadingSpinner message="Loading admin..." />;

  return (
    <div className="container py-4">
      <h2 className="mb-4"><i className="bi bi-gear me-2 text-primary"></i>Admin Dashboard</h2>

      {success && <div className="alert alert-success alert-dismissible">{success}<button className="btn-close" onClick={() => setSuccess('')}></button></div>}
      {error && <div className="alert alert-danger alert-dismissible">{error}<button className="btn-close" onClick={() => setError('')}></button></div>}

      <div className="row g-4">
        {/* Create Centre */}
        <div className="col-md-6">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-header bg-white"><h6 className="mb-0">Create Centre</h6></div>
            <div className="card-body">
              <form onSubmit={handleCreateCentre}>
                <div className="mb-2">
                  <input className="form-control" placeholder="Centre name" value={centreName} onChange={(e) => setCentreName(e.target.value)} required />
                </div>
                <div className="mb-2">
                  <input className="form-control" placeholder="Location" value={centreLocation} onChange={(e) => setCentreLocation(e.target.value)} required />
                </div>
                <button className="btn btn-primary btn-sm">Add Centre</button>
              </form>
            </div>
          </div>
        </div>

        {/* Create Test */}
        <div className="col-md-6">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-header bg-white"><h6 className="mb-0">Create Test</h6></div>
            <div className="card-body">
              <form onSubmit={handleCreateTest}>
                <div className="mb-2">
                  <input className="form-control" placeholder="Test name" value={testName} onChange={(e) => setTestName(e.target.value)} required />
                </div>
                <div className="mb-2">
                  <input className="form-control" placeholder="Description (optional)" value={testDesc} onChange={(e) => setTestDesc(e.target.value)} />
                </div>
                <button className="btn btn-primary btn-sm">Add Test</button>
              </form>
            </div>
          </div>
        </div>

        {/* Link Centre-Test with Price */}
        <div className="col-12">
          <div className="card shadow-sm border-0">
            <div className="card-header bg-white"><h6 className="mb-0">Link Test to Centre (Set Price)</h6></div>
            <div className="card-body">
              <form onSubmit={handleLinkCentreTest} className="row g-2 align-items-end">
                <div className="col-md-3">
                  <label className="form-label small">Centre</label>
                  <select className="form-select" value={ctCentreId} onChange={(e) => setCtCentreId(e.target.value)} required>
                    <option value="">Select centre</option>
                    {centres.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label small">Test</label>
                  <select className="form-select" value={ctTestId} onChange={(e) => setCtTestId(e.target.value)} required>
                    <option value="">Select test</option>
                    {tests.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label small">Price (Rs.)</label>
                  <input type="number" className="form-control" placeholder="500" value={ctPrice} onChange={(e) => setCtPrice(e.target.value)} min="1" required />
                </div>
                <div className="col-md-3">
                  <button className="btn btn-primary w-100">Link</button>
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Existing Centres */}
        <div className="col-md-6">
          <div className="card shadow-sm border-0">
            <div className="card-header bg-white"><h6 className="mb-0">Existing Centres ({centres.length})</h6></div>
            <ul className="list-group list-group-flush">
              {centres.map(c => (
                <li className="list-group-item d-flex justify-content-between" key={c.id}>
                  <span>{c.name}</span>
                  <small className="text-muted">{c.location}</small>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Existing Tests */}
        <div className="col-md-6">
          <div className="card shadow-sm border-0">
            <div className="card-header bg-white"><h6 className="mb-0">Existing Tests ({tests.length})</h6></div>
            <ul className="list-group list-group-flush">
              {tests.map(t => (
                <li className="list-group-item" key={t.id}>
                  {t.name} <small className="text-muted">— {t.description || 'No description'}</small>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Admin;
