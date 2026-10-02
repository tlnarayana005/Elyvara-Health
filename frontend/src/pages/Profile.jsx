import { useSelector } from 'react-redux';

function Profile() {
  const { user } = useSelector((state) => state.auth);

  return (
    <div className="container py-4" style={{ maxWidth: 500 }}>
      <h3 className="mb-4">
        <i className="bi bi-person-circle me-2 text-primary"></i>Profile
      </h3>
      <div className="card shadow-sm border-0">
        <div className="card-body">
          <div className="mb-3">
            <small className="text-muted d-block">Name</small>
            <strong>{user?.name}</strong>
          </div>
          <div className="mb-3">
            <small className="text-muted d-block">Email</small>
            <strong>{user?.email}</strong>
          </div>
          <div className="mb-3">
            <small className="text-muted d-block">Role</small>
            <span className={`badge bg-${user?.is_admin ? 'danger' : 'primary'}`}>
              {user?.is_admin ? 'Admin' : 'User'}
            </span>
          </div>
          <div>
            <small className="text-muted d-block">Member Since</small>
            {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
