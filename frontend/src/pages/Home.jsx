import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Zap, Shield, FileCheck, UploadCloud } from 'lucide-react';

export default function Home() {
  return (
    <div>
      <div className="dash-card-subtle" style={{ padding: '3rem 2rem', textAlign: 'center', marginBottom: '2rem' }}>
        <span style={{ 
          background: 'var(--primary-light)', 
          color: 'var(--primary-accent)', 
          padding: '0.4rem 1rem', 
          borderRadius: '9999px', 
          fontWeight: 700, 
          fontSize: '0.85rem' 
        }}>
          AI Notes Quality Analyzer
        </span>

        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, margin: '1rem 0 0.5rem 0' }}>
          Organize & Evaluate Your Notes with RecoMind
        </h1>
        
        <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto 1.5rem auto' }}>
          Upload handwritten or digital study documents and get instant quality scores, insights, and clean structured summaries.
        </p>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <Link to="/upload" className="btn-new" style={{ padding: '0.75rem 1.8rem' }}>
            <UploadCloud size={18} /> Upload Notes
          </Link>
          <Link to="/dashboard" className="btn-new" style={{ background: '#ffffff', color: 'var(--text-primary)', boxShadow: 'none', border: '1px solid var(--border-subtle)' }}>
            View Dashboard <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dash-card">
          <div className="stat-icon blue">
            <Zap size={22} />
          </div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Instant Upload & Store</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Supports PDF, JPG, JPEG, and PNG formats directly saved to Django backend media storage.
          </p>
        </div>

        <div className="dash-card">
          <div className="stat-icon purple">
            <FileCheck size={22} />
          </div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Text Extraction Ready</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Pre-built REST endpoints prepared for OCR integration in upcoming updates.
          </p>
        </div>

        <div className="dash-card">
          <div className="stat-icon sky">
            <Shield size={22} />
          </div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Decoupled REST API</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Clean React + Django REST Framework separation with CORS pre-configured.
          </p>
        </div>
      </div>
    </div>
  );
}
