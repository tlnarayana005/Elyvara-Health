import { Link } from 'react-router-dom';
import { useSelector } from 'react-redux';

function Home() {
  const { isAuthenticated } = useSelector((state) => state.auth);

  return (
    <>
      {/* Hero */}
      <section className="bg-primary text-white py-5">
        <div className="container text-center py-4">
          <h1 className="display-4 fw-bold mb-3">
            <i className="bi bi-heart-pulse me-2"></i>
            EVE Healthcare
          </h1>
          <p className="lead mb-4" style={{ maxWidth: 600, margin: '0 auto' }}>
            Book diagnostic tests at trusted centres near you. Fast, reliable, and affordable healthcare at your fingertips.
          </p>
          <div className="d-flex justify-content-center gap-3">
            {isAuthenticated ? (
              <Link to="/centres" className="btn btn-light btn-lg px-4">
                Browse Centres
              </Link>
            ) : (
              <>
                <Link to="/signup" className="btn btn-light btn-lg px-4">Get Started</Link>
                <Link to="/login" className="btn btn-outline-light btn-lg px-4">Login</Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-5">
        <div className="container">
          <h2 className="text-center mb-5">How It Works</h2>
          <div className="row g-4">
            {[
              { icon: 'bi-search', title: 'Find a Centre', desc: 'Browse diagnostic centres and compare test prices across locations.' },
              { icon: 'bi-calendar-check', title: 'Book a Test', desc: 'Select your test, pick an appointment time, and confirm your booking.' },
              { icon: 'bi-credit-card', title: 'Pay Online', desc: 'Complete your payment securely through our simulated payment system.' },
              { icon: 'bi-clipboard2-pulse', title: 'Get Results', desc: 'Track your booking status and receive confirmations instantly.' },
            ].map((f, i) => (
              <div className="col-md-6 col-lg-3" key={i}>
                <div className="card h-100 border-0 shadow-sm text-center p-4">
                  <i className={`bi ${f.icon} fs-1 text-primary mb-3`}></i>
                  <h5>{f.title}</h5>
                  <p className="text-muted small">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-dark text-white py-4 mt-auto">
        <div className="container text-center">
          <p className="mb-0 small">&copy; 2026 EVE Healthcare. Built for SDE Intern Assignment.</p>
        </div>
      </footer>
    </>
  );
}

export default Home;
