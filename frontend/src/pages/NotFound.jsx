import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="notfound-page" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
      <AlertTriangle size={64} style={{ color: '#ef4444', marginBottom: '1.5rem' }} />
      <h1 className="page-title" style={{ fontSize: '3rem' }}>404</h1>
      <h2 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Page Not Found</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', maxWidth: '400px', margin: '0 auto 2rem auto' }}>
        The page you are looking for does not exist or has been moved.
      </p>
      <Link to="/" className="btn btn-primary">
        <Home size={18} /> Back to Home
      </Link>
    </div>
  );
}
