function StatusBadge({ status }) {
  const colorMap = {
    PENDING: 'warning',
    CONFIRMED: 'success',
    SUCCESS: 'success',
    FAILED: 'danger',
    CANCELLED: 'secondary',
  };
  const color = colorMap[status] || 'info';
  return <span className={`badge bg-${color}`}>{status}</span>;
}

export default StatusBadge;
